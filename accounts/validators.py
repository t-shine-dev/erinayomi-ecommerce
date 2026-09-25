import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class ComplexPasswordValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Your password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Your password must contain at least one digit."),
                code='password_no_number',
            )
        if not re.search(r'[@$!%*?&^#()[\]{}<>+=_—|:;.,~`\'"-]', password):
            raise ValidationError(
                _("Your password must contain at least one special character/symbol."),
                code='password_no_symbol',
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 8 characters, including an uppercase letter, a number, and a symbol."
        )

    