"""Finite, bounded JSON decoding; no global interpreter settings are changed."""
import hashlib,json,math,sys
from decimal import Decimal,InvalidOperation
class DataFault(ValueError):pass
class NumericFault(DataFault):pass
MAX_FLOAT_GUARD=Decimal('1.8e308')
def number(token):
    if len(token)>128:raise NumericFault('FLOAT_TOKEN_LENGTH')
    try:
        d=Decimal(token)
        if not d.is_finite() or d.copy_abs()>MAX_FLOAT_GUARD:raise NumericFault('FLOAT_NONFINITE_OR_OVERFLOW')
        value=float(token)
    except (InvalidOperation,OverflowError,ValueError) as e:raise NumericFault('FLOAT_RANGE_REJECTED') from e
    if not math.isfinite(value):raise NumericFault('FLOAT_NONFINITE')
    return value

def integer(token):
    if len(token.lstrip('-'))>4300:raise NumericFault('INTEGER_TOKEN_LENGTH')
    try:return int(token)
    except ValueError as e:raise NumericFault('INTEGER_REJECTED') from e

def finite_tree(value,*,max_depth=48,max_nodes=10000):
    stack=[(value,0)];nodes=0
    while stack:
        x,depth=stack.pop();nodes+=1
        if depth>max_depth or nodes>max_nodes:raise DataFault('JSON_DEPTH_OR_NODE_LIMIT')
        if type(x) is float and not math.isfinite(x):raise NumericFault('NONFINITE_DECODED_NUMBER')
        if type(x) is dict:stack.extend((v,depth+1) for v in x.values())
        elif type(x) in (list,tuple):stack.extend((v,depth+1) for v in x)
    return value

def loads(text,*,max_bytes=1000000,max_depth=48,max_nodes=10000):
    if type(text) is bytes:
        try:text=text.decode('utf-8')
        except UnicodeError as e:raise DataFault('JSON_ENCODING') from e
    if type(text) is not str:raise DataFault('JSON_TEXT_TYPE')
    try:
        if len(text.encode('utf-8'))>max_bytes:raise DataFault('JSON_SIZE')
    except UnicodeError as e:raise DataFault('JSON_ENCODING') from e
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise DataFault('DUPLICATE_JSON_KEY')
            d[k]=v
        return d
    def constant(token):raise NumericFault('NONFINITE_JSON_CONSTANT')
    try:v=json.loads(text,object_pairs_hook=pairs,parse_float=number,parse_int=integer,parse_constant=constant)
    except DataFault:raise
    except (ValueError,TypeError,RecursionError) as e:raise DataFault('WHOLE_JSON_REQUIRED') from e
    return finite_tree(v,max_depth=max_depth,max_nodes=max_nodes)

def read(path):return loads(path.read_bytes(),max_bytes=64000000,max_depth=128,max_nodes=2000000)
def canonical(v):
    finite_tree(v,max_depth=128,max_nodes=2000000)
    try:return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
    except (ValueError,TypeError,UnicodeError,RecursionError) as e:raise DataFault('CANONICAL_JSON_REJECTED') from e

def sha(b):return hashlib.sha256(b).hexdigest()
