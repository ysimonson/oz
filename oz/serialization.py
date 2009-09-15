import cPickle
import simplejson
import types
import urllib
import datetime
import base64

COLLECTIONS = set, list, tuple
PRIMITIVES = str, unicode, int, float, bool, long, datetime.datetime, datetime.time, datetime.datetime, datetime.timedelta, datetime.tzinfo

def _is_object(obj):
    return isinstance(obj, object) and type(obj) is not types.TypeType and type(obj) is not types.FunctionType

def _flatten(obj):
    if type(obj) in PRIMITIVES:
        return str(obj)
        
    elif type(obj) in COLLECTIONS:
        return [_flatten(item) for item in obj]
        
    elif isinstance(obj, dict):
        new_dict = {}
        for key in obj: new_dict[key] = _flatten(obj[key])
        return new_dict
        
    elif _is_object(obj):
        new_obj = {}
        
        for key in dir(obj):
            if key.startswith('_'): continue
            
            value = getattr(obj, key)
            if type(value) is types.FunctionType: continue
            
            new_obj[key] = _flatten(value)
            
        return new_obj
    
def _to_xml(obj):
    obj = _flatten(obj)
    return ('text/xml', '<stub/>')

def _to_json(obj):
    obj = _flatten(obj)
    #TODO
    #return ('application/json', simplejson.dumps(obj))
    return ('text/javascript', simplejson.dumps(obj))
        
def serialize(handler, obj):
    try:
        format = handler.get_argument('format')
    except HTTPError, e:
        handler.require_setting('default_format')
        format = handler.application.settings.get('default_format')
    
    if format in SERIALIZERS:
        serializer = SERIALIZERS[format]
    else:
        format = SERIALIZERS['__default__']
    
    (content_type, content) = serializer(obj)
    handler.set_header('Content-Type', content_type)
    handler.write(content)

SERIALIZERS = {
    '__default__': _to_json,
    'json': _to_json,
    'xml': _to_xml
}