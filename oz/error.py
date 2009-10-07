# portions adapted from Django <djangoproject.com> and web.py <webpy.org>
# Copyright (c) 2005, the Lawrence Journal-World
# Used under the modified BSD license:
# http://www.xfree86.org/3.3.6/COPYRIGHT2.html#5

from tornado import escape
import sys, urlparse, pprint, traceback
import os, os.path, base64

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

whereami = os.path.join(os.getcwd(), __file__)
whereami = os.path.sep.join(whereami.split(os.path.sep)[:-1])
 
class BaseObject(object): pass
class DebugBreakException(Exception): pass

def _dict_to_list(d):
    items = d and d.items() or []
    items.sort()
    return items

def dicttable(d, kls='req', id=None):
    return dicttable_items(_dict_to_list(d), kls, id)
        
def dicttable_items(items, kls='req', id=None):
    output = ''
    
    if items:
        output += '<table class="%s"' % kls
        if id: output += 'id="%s"' % id
        output += '><thead><tr><th>Variable</th><th>Value</th></tr></thead><tbody>'
        
        for k, v in items:
            try:
                output += '<tr><td>%s</td><td class="code"><div>%s</div></td></tr>' \
                          % (k, prettify(v))
            except UnicodeDecodeError, e:
                output += '<tr><td>%s (in base 64)</td><td class="code"><div>%s</div></td></tr>' \
                          % (k, base64.b64encode(v))
                
        output += '</tbody></table>'
    else:
        output += '<p>No data.</p>'
        
    return output

def dicttable_txt(d, tabbing):
    return dicttable_items_txt(_dict_to_list(d), tabbing)
    
def dicttable_items_txt(items, tabbing):
    if len(items) == 0: return ''
    
    formatted_items = []
    max_key_length = 0
    
    for i in range(0, len(items)):
        k = items[i][0]
        v = items[i][1]
        
        try:
            formatted_items.append([k, unicode(v)])
        except UnicodeDecodeError:
            k += ' (in base 64)'
            formatted_items.append([k, base64.b32encode(v)])
        
        if len(k) > max_key_length: max_key_length = len(k)
    
    tabbing = ' ' * tabbing
    output = ''
        
    for k, v in formatted_items:
        spaces = ' ' * (max_key_length - len(k))
        output += '%s%s%s = %s\n' % (tabbing, k, spaces, v)
        
    return output

def prettify(x):
    try:
        out = pprint.pformat(unicode(x))
    except UnicodeDecodeError, e:
        raise e
    except Exception, e: 
        out = '[could not display: <' + e.__class__.__name__ + \
              ': '+str(e)+'>]'
    return out

def _get_lines_from_file(filename, lineno, context_lines):
    """
    Returns context_lines before and after lineno from file.
    Returns (pre_context_lineno, pre_context, context_line, post_context).
    """
    
    try:
        source = open(filename).readlines()
        lower_bound = max(0, lineno - context_lines)
        upper_bound = lineno + context_lines

        pre_context = \
            [line.strip('\n') for line in source[lower_bound:lineno]]
        context_line = source[lineno].strip('\n')
        post_context = \
            [line.strip('\n') for line in source[lineno + 1:upper_bound]]

        return lower_bound, pre_context, context_line, post_context
    except (OSError, IOError):
        return None, [], None, []
        
def _get_frames(tback, is_debug):
    frames = []
    
    while tback is not None:
        if tback.tb_next == None and is_debug: break
        
        filename = tback.tb_frame.f_code.co_filename
        function = tback.tb_frame.f_code.co_name
        lineno = tback.tb_lineno - 1
        pre_context_lineno, pre_context, context_line, post_context = \
            _get_lines_from_file(filename, lineno, 7)
        
        frame = BaseObject()
        frame.tback = tback
        frame.filename = filename
        frame.function = function
        frame.lineno = lineno
        frame.vars = tback.tb_frame.f_locals
        frame.id = id(tback)
        frame.pre_context = pre_context
        frame.context_line = context_line
        frame.post_context = post_context
        frame.pre_context_lineno = pre_context_lineno
        frames.append(frame)
        
        tback = tback.tb_next
    
    return frames

def _get_response_output(handler):
    if handler._write_buffer:
        response_output = "".join(handler._write_buffer)
        
        if response_output:
            # Don't write out empty chunks because that means
            # END-OF-STREAM with chunked encoding
            for transform in handler._transforms:
                response_output = transform.transform_chunk(response_output)
    else:
        response_output = ''
        
    return response_output

def _get_response_headers(handler):
    return [(k, v) for (k, v) in handler._headers.iteritems()]

def render_html(handler):
    exception_type, exception_value, tback = sys.exc_info()
    is_debug = isinstance(exception_value, DebugBreakException)
    
    frames = _get_frames(tback, is_debug)
    frames.reverse()
    
    if is_debug:
        exception_type = 'Debug breakpoint'
        exception_value = ''
        
    urljoin = urlparse.urljoin
    
    params = {
        'exception_type': exception_type,
        'exception_value': exception_value,
        'frames': frames,
        
        'request_input': handler.request.body,
        'request_cookies': handler.cookies,
        'request_headers': handler.request.headers,
        
        'request_path': handler.request.uri,
        'request_method': handler.request.method,
        'response_output': _get_response_output(handler),
        'response_headers': _get_response_headers(handler),
        
        'dict': dict,
        'str': str,
        'prettify': prettify,
        'dicttable': dicttable,
        'dicttable_items': dicttable_items
    }
    
    return handler.render_string('error_template.html', **params)
    
def render_txt(handler):
    return traceback.format_exc()
    
def _writeln(handler, text):
    handler.write(text)
    handler.write('\n')
    
def render_verbose_txt(handler):
    exception_type, exception_value, tback = sys.exc_info()
    is_debug = isinstance(exception_value, DebugBreakException)
    frames = _get_frames(tback, is_debug)
    
    buffer = StringIO()
    
    _writeln(buffer, 'Error:  ' + str(exception_type))
    _writeln(buffer, 'Desc:   ' + str(exception_value))
    _writeln(buffer, '*' * 80)
    
    _writeln(buffer, 'Traceback (most recent call last):')
    for frame in frames:
        _writeln(buffer, '  File "%s", line %s, in %s' % (frame.filename, frame.lineno, frame.function))
        if frame.context_line: _writeln(buffer, '    ' + frame.context_line.strip())
        if frame.vars: _writeln(buffer, dicttable_txt(frame.vars, 6))
    
    _writeln(buffer, 'Response headers:')
    _writeln(buffer, dicttable_items_txt(_get_response_headers(handler), 0))
    
    _writeln(buffer, '\nResponse body:')
    _writeln(buffer, _get_response_output(handler))
    
    _writeln(buffer, '*' * 80)
    _writeln(buffer, '\nRequest input:')
    _writeln(buffer, handler.request.body)
    
    _writeln(buffer, '\nRequest cookies:')
    _writeln(buffer, dicttable_txt(handler.cookies, 0))
    
    return buffer.getvalue()