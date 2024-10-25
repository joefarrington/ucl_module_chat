from jinja2 import Template

module_template = Template(
    """
# {{ module_title }} ({{module_code}})

## Key information

**Course Code:** {{ module_code }} \\
**Subject Area:** {{ subject }} \\
**Keywords:** {{ keywords }} \\
**Module catalogue URL:** {{ url }}  

**Faculty:** {{ faculty }} \\
**Teaching Department:** {{ teaching_department }} \\
**Credit Value:** {{ credit_value }} \\
**Restrictions:** {{ restrictions }}

## Alternative credit options
{{ alternative_credit_options }}

## Description
{{ description }}

## Module deliveries for 2024/25 academic year
{% for delivery in deliveries %}
### {{delivery.type}} (FHEQ Level {{delivery.fheq_level}})

#### Teaching and assessment
**Intended teaching term:** {{ delivery.teaching_term }} \\
**Mode of study:** {{ delivery.mode_of_study }} \\
**Methods of assessment:** {{ delivery.methods_of_assessment }} \\
**Mark scheme:** {{ delivery.mark_scheme }}

#### Other information
**Number of students on module in previous year:** {{ delivery.number_of_students_prior_year }} \\
**Who to contact for more information:** {{ delivery.contact_email }}
{% endfor %}
"""
)
