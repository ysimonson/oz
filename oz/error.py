from tornado import escape
import sys, urlparse, pprint, traceback 
import os, os.path

whereami = os.path.join(os.getcwd(), __file__)
whereami = os.path.sep.join(whereami.split(os.path.sep)[:-1])
 
class BaseObject(object): pass

def dicttable(d, kls='req', id=None):
    items = d and d.items() or []
    items.sort()
    return dicttable_items(items, kls, id)
        
def dicttable_items(items, kls='req', id=None):
    output = ''
    
    if items:
        output += '<table class="%s"' % kls
        if id: output += 'id="%s"' % id
        output += '><thead><tr><th>Variable</th><th>Value</th></tr></thead><tbody>'
        
        for k, v in items:
                output += '<tr><td>%s</td><td class="code"><div>%s</div></td></tr>' \
                          % (k, prettify(v))
                
        output += '</tbody></table>'
    else:
        output += '<p>No data.</p>'
        
    return output

def prettify(x):
    try: 
        out = pprint.pformat(x)
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

def render_error(handler):
    exception_type, exception_value, tback = sys.exc_info()
    frames = []
    
    while tback is not None:
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
        
    frames.reverse()
    urljoin = urlparse.urljoin
    
    if handler._write_buffer:
        response_output = "".join(handler._write_buffer)
        
        if response_output:
            # Don't write out empty chunks because that means
            # END-OF-STREAM with chunked encoding
            for transform in handler._transforms:
                response_output = transform.transform_chunk(response_output)
    else:
        response_output = ''
    
    params = {
        'exception_type': exception_type,
        'exception_value': exception_value,
        'frames': frames,
        
        'request_input': handler.request.body,
        'request_cookies': handler.cookies,
        'request_headers': handler.request.headers,
        
        'request_path': handler.request.uri,
        'request_method': handler.request.method,
        'response_output': response_output,
        'response_headers': [(k, v) for (k, v) in handler._headers.iteritems()],
        
        'dict': dict,
        'str': str,
        'prettify': prettify,
        'dicttable': dicttable,
        'dicttable_items': dicttable_items
    }
    
    handler.render('error_template.html', **params)