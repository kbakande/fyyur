from wtforms.validators import ValidationError
from flask import flash
import re


def customAnyOf(values):
  message = 'Invalid value, must be one of: {0}.'.format( ','.join(values) )
  def _validate(form, field):
    error = False
    for value in field.data:
      if value not in values:
        error = True
    if error:
      raise ValidationError(message)
  return _validate


def phoneAnyOf(phoneValues):
  message = 'Invalid value, must be one of: {0}.'.format( ','.join(phoneValues))
  def _validate(form, field):
    phoneMatch  = re.fullmatch(r"[0-9]\d\d-[0-9]\d\d-[0-9]\d\d\d", field.data)
    if not phoneMatch:
        raise ValidationError(message)
  return _validate

def flash_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')