from flask_wtf import FlaskForm
from flask import render_template
from wtforms.widgets import TextArea, TextInput, Select
from wtforms.fields import HiddenField, FileField, SelectMultipleField
from wtforms import fields, widgets, Form
from markupsafe import Markup
from itertools import chain
from hashlib import sha256
from wtforms.validators import StopValidation
from wtforms.utils import unset_value
import json
from .markup import element, button, link_button, GridColumn



class OrderedForm(FlaskForm):
    def __iter__(self):
        fields = list(super(OrderedForm, self).__iter__())
        field_order = getattr(self, 'field_order', None)
        if field_order:
            temp_fields = []
            for name in field_order:
                if name == '*':
                    temp_fields.extend([f for f in fields
                                        if f.name not in field_order])
                else:
                    temp_fields.append([f for f in fields
                                        if f.name == name][0])
            fields =temp_fields
        return iter(fields)
        
    field_order = ['*','ok']

field_renderers = {}

class FieldRenderer(object):
    __slots__ = ["view", "field", "kwargs", "form_info"]
    def __init__(self, view, field, form_info=None, **kwargs):
        self.view = view
        self.field = field
        self.kwargs = kwargs
        self.form_info = form_info

    def render_input(self):
        args = self.view.get_field_args(self.field)
        args.update(self.kwargs)
        if self.field.errors:
            args["class"] = args.get("class", "") + " is-invalid"
        return Markup(self.field(**args))

    def render_errors(self):
        if self.field.errors:
            return Markup("").join((element("p", self.view.error_attrs, i)
                                    for i in self.field.errors))
        else:
            return ""

    def render_description(self):
        if self.field.description:
            return element("p", self.view.description_attrs,
                           self.field.description)
        else:
            return ""

    def render_label(self):
        return self.field.label(**self.view.label_args)
    
    def __html__(self):
        try:
            if self.field.widget.suppress_form_decoration:
                return self.field.widget(self.field)
        except:
            pass

        if self.view.want_labels:
            l = self.render_label()
            

            if l is None:
                field_div_attrs = self.view.field_div_attrs_no_label
                l = ""
            else:
                field_div_attrs = self.view.field_div_attrs
        else:
            field_div_attrs = self.view.field_div_attrs
            l = ""
        
        i = Markup("{}{}{}").format(self.render_input(),
                                    self.render_description(),
                                    self.render_errors())
        
        if field_div_attrs:
            i = element("div", field_div_attrs, i)

        return l+i

class FormButton(object):
    __slots__ = ["content"]
    
    def __init__(self, content, **kwargs):
        self.content = content

    def __html__(self):
        return self.render(view=None, form_info=None)
        
class SubmitButton(FormButton):
    __slots__ = ["name", "value", "action", "context_class"]
    
    def __init__(self, text,
                 name=None,
                 value=None,
                 action=None,
                 context_class="primary",
                 **kwargs):
        super(SubmitButton, self).__init__(content=text, **kwargs)
        self.name = name
        self.value = value
        self.action = action
        self.context_class = context_class
        
    def render(self, view, form_info=None):
        attrs = {"type": "submit"}
        
        if self.name is not None:
            attrs["name"] = self.name
        if self.value is not None:
            attrs["value"] = self.value
        if self.action is not None:
            attrs["formaction"] = self.action
            
        return button(self.content,
                      context_class=self.context_class,
                      attrs=attrs)

class ButtonGroup(FormButton):
    def get_div_attrs(self):
        return {"class": "btn-group"}
    
    def render(self, view, **kwargs):
        if not self.content:
            return ""
        
        c = Markup("").join((i.render(self) if isinstance(i, FormButton) else i
                             for i in self.content))
        return element("div", self.get_div_attrs(), c)
        
        
class FormView(object):
    want_labels = True
    
    def __init__(self,
                 buttons=None,
                 method="POST",
                 field_order=None,
                 **kwargs):
        self.field_renderers = {}
        self.label_args = {}
        self.field_div_attrs = None
        self.field_div_attrs_no_label = None
        self.form_attrs = {}
        self.button_bar_attrs = {}
        self.method = method
        self.error_attrs = {}
        self.description_attrs = {}
        self.field_order = field_order
        if buttons is None:
            self.buttons = [SubmitButton("OK")]
        else:
            self.buttons = buttons
        
    def get_field_args(self, field):
        return {}
            
    def render_field(self, field, form_info=None, **kwargs):
        try:
            if field.widget.suppress_form_decoration:
                return field.widget(field)
        except:
            pass

        if field.type in field_renderers:
            r = field_renderers[field.type]
        elif hasattr(field, 'renderer'):
            r = field.renderer
        else:
            r = FieldRenderer
        return r(self, field, form_info=form_info, **kwargs)

    def render_fields(self, fields, form_info=None, **kwargs):
        l = []
        if self.field_order:
            for i in self.field_order:
                l.append(self.render_field(fields[i],
                                           form_info=form_info,
                                           **kwargs))                
        else:
            for i in fields:
                if isinstance(i, HiddenField):
                    continue
                l.append(self.render_field(i,
                                           form_info=form_info,
                                           **kwargs))
            
        return Markup("").join(l)

    def hidden_errors(self, form):
        l = (Markup("").join((Markup('<p class="invalid-feedback">{}</p>').format(j)
                              for j in i.errors))
             for i in form if isinstance(i, HiddenField))
        return Markup("").join(l)
    
    def render(self, form, form_info=None):
        contents=Markup("{}{}{}{}").format(
            form.hidden_tag(),
            self.hidden_errors(form),
            self.render_fields(form, form_info=form_info),
            self.render_footer(form_info=form_info)
        )
        
        attrs = dict(self.form_attrs)
        if any((isinstance(i, FileField) for i in form)):
            attrs["enctype"] = "multipart/form-data"

        attrs["method"] = self.method
            
        return element("form", attrs, contents)

    def render_footer(self, form_info=None):
        if not self.buttons:
            return ""
        
        c = Markup("").join((i.render(self, form_info=form_info)
                             if isinstance(i, FormButton) else i
                             for i in self.buttons))
        return element("div", self.button_bar_attrs, c)

    def get_formfield_view(self):
        return self
    
    def __call__(self, form, form_info=None):
        return RenderProxy(self, form, form_info=form_info)

class RenderProxy(object):
    __slots__ = ["obj", "args", "kwargs"]
    
    def __init__(self, obj, *args, **kwargs):
        self.obj = obj
        self.args = args
        self.kwargs = kwargs
        
    def __html__(self):
        return self.obj.render(*self.args, **self.kwargs)

def field_renderer(t):
    def wrap(cls):
        field_renderers[t] = cls
        return cls
    return wrap

@field_renderer('RadioField')
class RadioFieldRenderer(FieldRenderer):
    def render_input(self):
        itms = (Markup('<div class="radio"><label>{} {}</label></div>').
                format(Markup(i), Markup(i.label.text))
                for i in self.field)
        return Markup("").join(itms)


@field_renderer('SubmitField')
class SubmitFieldRenderer(FieldRenderer):
    def render_label(self):
        return None

@field_renderer('BooleanField')
class BooleanFieldRenderer(FieldRenderer):
    def render_input(self):
        return Markup(self.field(**self.kwargs))
        
    def __html__(self):
        l = ""
        if self.view.label_args:
            l = element("div", self.view.label_args, "")

        i = Markup('<div class="checkbox"><label>{} {}</label>{}{}</div>')\
            .format(self.render_input(),
                    self.field.label.text,
                    self.render_description(),
                    self.render_errors())
        
        if self.view.field_div_attrs:
            i = element("div", self.view.field_div_attrs, i)

        return l+i

@field_renderer('FormField')
class FormFieldRenderer(FieldRenderer):
    def render_input(self):
        v = self.view.get_formfield_view()
        c = Markup("{}{}").format(self.field.hidden_tag(),
                                     v.render_fields(self.field,
                                                     form_info=self.form_info))
        return element("div", v.form_attrs, c)
        
    def render_errors(self):
        return ""

    def render_label(self):
        if self.field.label.text == "":
            return None
        else:
            return self.field.label(**self.view.label_args)

@field_renderer('MultiCheckboxField')
class MultiCheckboxFieldRenderer(FieldRenderer):
    def render_input(self):
        c = Markup("").join(Markup('<li class="checkbox"><label>{} {}</label></li>')\
                            .format(i(),
                                    i.label.text) for i in self.field)
        return element("ul", {"class": "unstyled"}, c)
    
class VerticalFormView(FormView):
    formfield_view = None
    
    def __init__(self, formfield_view=None, **kwargs):
        super(VerticalFormView, self).__init__(**kwargs)
        if any((isinstance(i, ButtonGroup) for i in self.buttons)):
            self.button_bar_attrs = {"class": "btn-toolbar"}
        self.error_attrs = {"class": "form-text invalid-feedback"}
        self.description_attrs = {"class": "form-text"}
        if formfield_view is not None:
            self.formfield_view = formfield_view
    
    def render_field(self, field, **kwargs):
        try:
            if field.widget.suppress_form_decoration:
                return field.widget(field)
        except:
            pass

        cls = "form-group"
        #if field.errors:
        #    cls += " text-danger"
        if field.flags.required:
            cls += " required"
            
        return element("div", {"class": cls},
                       super(VerticalFormView, self).render_field(field,
                                                                  **kwargs)) 
    def get_field_args(self, field):
        return {"class": "form-control"}

    def get_formfield_view(self):
        return self.formfield_view or HorizontalFormView()

    
class HorizontalFormView(VerticalFormView):
    def __init__(self, widths=[2, 10], size="md", **kwargs):
        super(HorizontalFormView, self).__init__(**kwargs)
        self.label_args= {"class": "col-form-label col-{}-{}".format(size,
                                                                    widths[0])}
        self.field_div_attrs = {"class": "col-{}-{}".format(size, widths[1])}
        self.field_div_attrs_no_label = {
            "class": "col-{}-{} col-{}-offset-{}".format(size, widths[1],
                                                         size, widths[0])
        }
        self.form_attrs = {"class": "form-horizontal"}

    def render_field(self, field, **kwargs):
        try:
            if field.widget.suppress_form_decoration:
                return field.widget(field)
        except:
            pass

        cls = "form-group row"
        if field.errors:
            cls += " has-error"
        if field.flags.required:
            cls += " required"
            
        return element("div", {"class": cls},
                       super(VerticalFormView, self).render_field(field,
                                                                  **kwargs)) 

    def render_footer(self, form_info=None):
        f = super(HorizontalFormView, self).render_footer(form_info=form_info)
        if not f:
            return ""
        
        return element("div", {"class": "form-group"},
                       element("div", self.field_div_attrs_no_label, f))
        
class FormPart(object):
    __slots__ = ["fields", "view", "name", "title"]
    def __init__(self, title, view, fields=None, name=None):
        self.title = title
        self.view = view
        if fields is None:
            self.fields = view.get_owned_fields()
        else:
            self.fields = fields

        if name is None:
            self.name = "form-part-" + sha256(title.encode("utf-8")).hexdigest()
        else:
            self.name = name
            
    def get_owned_fields(self):
        return self.fields

    def filter_own_fields(self, fields):
        own = []
        own_set = set()
        rest = []

        for i in self.get_owned_fields():
            if i[-1] == '*':
                for j in fields:
                    if j.name.startswith(i[:-1]):
                        own.append(j)
                        own_set.add(j)
            else:
                for j in fields:
                    if j.name == i:
                        own.append(j)
                        own_set.add(j)

        rest = [i for i in fields if i not in own_set]

        return own, rest
    
class HierarchicalFormView(FormView):
    def __init__(self, rest_view=None, **kwargs):
        super(HierarchicalFormView, self).__init__(**kwargs)
        self.rest_view = rest_view
        self.parts = []
        
    def get_owned_fields(self):
        return chain(*(i.get_owned_fields() for i in self.tabs))

    def add_part(self, part):
        self.parts.append(part)
