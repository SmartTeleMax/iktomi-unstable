import re
from iktomi.forms.convs import *
from iktomi.utils import N_


class Email(Char):

    regex = re.compile(
        # dot-atom
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
        # Although quoted variant is allowed by spec it's actually not used
        # except by geeks that are looking for problems. But the characters
        # allowed in quoted string are not safe for HTML and XML, so quoted
        # e-mail can't be expressed in such formats directly which is quite
        # common. We prefer to forbid such valid but unsafe e-mails to avoid
        # security problems. To allow quoted names disable non-text characters
        # replacement and uncomment the following lines of regexp:
        ## quoted-string
        #r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|'
        #    r'\\[\001-011\013\014\016-\177])*"'
        r')@(?:[A-Z0-9-]+\.)+[A-Z]{2,6}$', re.IGNORECASE)
    error_regex = N_('incorrect e-mail address')


class ModelDictConv(Converter):
    '''Converts a dictionary to object of `model` class with the same fields.
    It is designed for use in FieldSet'''

    model = None

    def from_python(self, value):
        result = {}
        for field in self.field.fields:
            result[field.name] = getattr(value, field.name)
        return result

    def to_python(self, value):
        obj = self.model()
        for field in self.field.fields:
            setattr(obj, field.name, value[field.name])
        return obj


class OptionLabel(unicode):

    published = False


class ModelChoice(EnumChoice):

    condition = None
    conv = Int(required=False)
    title_field = 'title'

    def __init__(self, *args, **kwargs):
        EnumChoice.__init__(self, *args, **kwargs)
        self.conv = self.conv(field=self.field)

    @property
    def query(self):
        query = self.env.db.query(self.model)
        if isinstance(self.condition, dict):
            query = query.filter_by(**self.condition)
        elif self.condition is not None:
            query = query.filter(self.condition)
        return query

    def from_python(self, value):
        if value is not None:
            return self.conv.from_python(value.id)
        else:
            return ''

    def to_python(self, value):
        try:
            value = self.conv.to_python(value)
        except ValidationError:
            return None
        else:
            if value is not None:
                return self.query.filter_by(id=value).first()

    def get_object_label(self, obj):
        label = OptionLabel(getattr(obj, self.title_field))
        try:
            label.published = obj.publish
        except AttributeError:
            pass
        return label

    def get_label(self, form_value):
        obj = self._safe_to_python(form_value)
        if obj is not None:
            return self.get_object_label(obj)

    def options(self):
        for obj in self.query.all():
            yield self.conv.from_python(obj.id), self.get_object_label(obj)
