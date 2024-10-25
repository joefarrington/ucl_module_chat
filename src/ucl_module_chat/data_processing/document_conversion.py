import re
from pathlib import Path

import hydra
import jinja2
import omegaconf
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

from ucl_module_chat.data_processing.document_templates import module_template
from ucl_module_chat.utils.resolve_paths import get_abs_path_using_repo_root


def _extract_module_info_from_html(module_html: str) -> dict:
    """Parse HTML content for a UCL module page and extract key information."""

    soup = BeautifulSoup(module_html, "html.parser")

    # Extract the module title and code from the og:title meta tag
    pattern = r"""
    (?P<module_title>.*?)                # Capture the module title
    \s*                                  # Optional whitespace
    \((?P<module_code>[A-Z]{4}\d{4})\)   # Capture the alphanumeric code
    """
    og_title = soup.find("meta", attrs={"name": "og:title"})["content"]
    match = re.search(pattern, og_title, re.VERBOSE)
    module_title = match.group("module_title").strip()
    module_code = match.group("module_code").strip()

    url = soup.find("meta", attrs={"property": "og:url"})["content"]

    faculty = soup.find("meta", attrs={"name": "ucl:sanitized_faculty"})["content"]

    teaching_department = soup.find(
        "meta", attrs={"name": "ucl:sanitized_teaching_department"}
    )["content"]

    level = soup.find("meta", attrs={"name": "ucl:sanitized_level"})["content"]

    teaching_term = soup.find(
        "meta", attrs={"name": "ucl:sanitized_intended_teaching_term"}
    )["content"]

    credit_value = soup.find("meta", attrs={"name": "ucl:sanitized_credit_value"})[
        "content"
    ]

    sanitized_subject = soup.find("meta", attrs={"name": "ucl:sanitized_subject"})[
        "content"
    ]

    sanitized_keywords = soup.find("meta", attrs={"name": "ucl:sanitized_keywords"})[
        "content"
    ]

    restrictions = (
        soup.find("dt", string="Restrictions")
        .find_next_sibling("dd")
        .get_text()
        .strip()
        .replace("\n", " ")
    )

    alternative_credit_options = (
        soup.find("h2", string="Alternative credit options")
        .find_next("p")
        .get_text()
        .strip()
    )

    description = soup.find("div", class_="module-description").get_text()

    # Deliveries - there may be multiple deliveries for a module
    potential_deliveries = soup.find_all("div", class_="box tagged box--bar-thick")
    deliveries = [
        d
        for d in potential_deliveries
        if d.find("h3", string="Teaching and assessment") is not None
    ]
    collated_d = []
    for d in deliveries:
        delivery_info = {}

        # Info from the header
        header = d.find("h2").get_text()
        # Might need to modify this regex pattern if some modules are different
        pattern = r"""
            Intended\steaching\sterm:               # Matches 'Intended teaching term:'
            \s*                                     # Optional whitespace
            (?P<term>[\w\s,\(\)]+)                  # Capture the term
            \s*                                     # Optional whitespace
            (?P<type>Undergraduate|Postgraduate)    # Matches UG or PG
            \s*                                     # Optional whitespace
            \(FHEQ\sLevel\s(?P<fheq_level>\d+)\)    # Matches 'FHEQ Level X' 
            """  # and captures level number

        # Search for matches in the header string
        match = re.search(pattern, header, re.VERBOSE)

        if match:
            # Extracted values from the regex groups
            delivery_info["teaching_term"] = match.group("term").strip()
            delivery_info["type"] = match.group("type").strip()
            delivery_info["fheq_level"] = match.group("fheq_level").strip()

        # Info from the table for this delivery
        col_1 = d.find("section", class_="middle-split__column1")

        delivery_info["mode_of_study"] = (
            col_1.find("dt", string="Mode of study").find_next("dd").text.strip()
        )

        assessment_methods = (
            col_1.find("dt", string="Methods of assessment")
            .find_next("dd")
            .find_all("div")
        )
        delivery_info["methods_of_assessment"] = ", ".join(
            [" ".join(method.text.strip().split()) for method in assessment_methods]
        )

        delivery_info["mark_scheme"] = (
            col_1.find("dt", string="Mark scheme").find_next("dd").text.strip()
        )

        col_2 = d.find("section", class_="middle-split__column2")

        email = col_2.find("a", href=re.compile(r"^mailto:"))
        delivery_info["contact_email"] = email.text.strip() if email else None

        delivery_info["number_of_students_prior_year"] = (
            col_2.find("dt", string="Number of students on module in previous year")
            .find_next("dd")
            .text.strip()
        )

        collated_d.append(delivery_info)

    info = {
        "module_title": module_title,
        "module_code": module_code,
        "url": url,
        "faculty": faculty,
        "teaching_department": teaching_department,
        "level": level,
        "teaching_term": teaching_term,
        "credit_value": credit_value,
        "subject": sanitized_subject,
        "keywords": sanitized_keywords,
        "alternative_credit_options": alternative_credit_options,
        "description": description,
        "restrictions": restrictions,
        "deliveries": collated_d,
    }

    return info


def _module_info_to_markdown(module_info: dict, template: jinja2.Template) -> str:
    """Process module information dictionary into markdown document using template."""
    return template.render(module_info)


def _convert_module_html_to_markdown(
    module_html: str, extract_function: callable, markdown_template: jinja2.Template
) -> None:
    """Convert a single UCL module HTML page to a markdown document."""
    module_info = extract_function(module_html)
    module_markdown = _module_info_to_markdown(module_info, markdown_template)
    return module_markdown


def convert_all_documents_html_to_markdown(
    input_dir: str | Path,
    output_dir: str | Path,
    extract_function: callable = _extract_module_info_from_html,
    markdown_template: jinja2.Template = module_template,
):
    """Convert all UCL module HTML pages in a directory to markdown documents."""

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("""Converting HTML module files to markdown documents""")

    all_module_html_files = list(input_dir.glob("*.html"))

    n_modules = len(all_module_html_files)

    logger.info(
        f"Identified {n_modules} HTML module files to convert to markdown documents"
    )

    errors = 0
    for module_html_path in tqdm(all_module_html_files):
        try:
            with open(module_html_path, "r") as f:
                module_html = f.read()

            module_markdown = _convert_module_html_to_markdown(
                module_html, extract_function, markdown_template
            )

            output_path = output_dir / f"{module_html_path.stem}.md"
            with open(output_path, "w") as f:
                f.write(module_markdown)
        except Exception as e:
            errors += 1
            logger.error(f"Error converting {module_html_path.stem}: {e}")
    logger.info(f"{n_modules - errors} HTML files successfully converted to markdown")
    logger.info(f"{errors} HTML files could not be converted.")


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: omegaconf.DictConfig) -> None:
    """Run the document conversion process."""
    cfg = cfg.setup.convert_documents
    cfg.input_dir = get_abs_path_using_repo_root(cfg.input_dir)
    cfg.output_dir = get_abs_path_using_repo_root(cfg.output_dir)

    convert_all_documents_html_to_markdown(**cfg)


if __name__ == "__main__":
    main()
