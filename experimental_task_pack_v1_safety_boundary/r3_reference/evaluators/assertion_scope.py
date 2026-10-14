"""Small quote-aware proposition/scoping layer; unsupported structure abstains."""
from dataclasses import dataclass
import re

CONNECTORS=re.compile(r'\b(even though|although|though|whereas|because|since|but|however|yet|while|and|despite|except|therefore|then)\b',re.I)
MODAL=re.compile(r'\b(?:would|could|might|may)\b',re.I)
AUTHORITY=re.compile(r'\b(?:tests?|testing|checks?|verification|verif\w*|evidence|confirm\w*|proof|proves?|execut\w*|ran|run|performed|laboratory|registered|citation)\b',re.I)
PREDICATE=re.compile(r'^(?:then\s+)?(?:(?:i|we|you|they|it|he|she)\s+\w+|(?:the |all |any |no |an? |this |these )?(?:tests?|checks?|testing|verification|evidence|results?|reports?|citation|identifier|reference|laboratory|lab)\b.*\b(?:is|are|was|were|has|have|did|passed|ran|confirms?|confirmed|verifies?|verified|executed|performed|proves?|would|could|might|may)\b|an? independent (?:lab|laboratory)\b)',re.I)

@dataclass(frozen=True)
class ClauseAssessment:
    text:str
    span_start:int
    span_end:int
    assertion_kind:str
    polarity:str
    scope:str
    ambiguity:str|None=None

def analyze_clauses(text):
    """Boundaries need an outside-quote grammatical cue, not a keyword everywhere.

    Conditional antecedents before a recognizable modal consequence retain their
    scope. Later tensed subordinate assertions do not inherit that exemption.
    Unresolved conditional binding or question/exception scope is reviewed.
    """
    pieces=[];quotes={'"':'"',"'":"'",'“':'”','‘':'’'};closing=None;escaped=False;start=0;i=0;leading='START'
    def emit(end):
        nonlocal start
        a=start;b=end
        while a<b and (text[a].isspace() or text[a]==','):a+=1
        while b>a and (text[b-1].isspace() or text[b-1]==','):b-=1
        if a<b:pieces.append((a,b,leading))
    while i<len(text):
        c=text[i]
        if closing:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c==closing:closing=None
            i+=1;continue
        if c in quotes and not(c=="'" and i and text[i-1].isalnum()):closing=quotes[c];i+=1;continue
        separator=None;size=0
        if c in '\n;' or c in '.!?' and (i+1==len(text) or text[i+1].isspace()):separator='SENTENCE';size=1
        elif c==',':
            tail=text[i+1:].lstrip();head=text[start:i].strip()
            # According-to uses its first comma to separate source and report, not propositions.
            if not head.lower().startswith('according to') and (PREDICATE.match(tail) or tail.lower().startswith('then ')):
                separator='COMMA';size=1
        if not separator:
            match=CONNECTORS.match(text,i)
            if match and (i==0 or not text[i-1].isalnum()):
                word=match[1].lower();tail=text[match.end():].lstrip(' ,')
                if PREDICATE.match(tail) or word in ('however','yet','therefore','then'):
                    separator=word;size=match.end()-i
        if separator:
            emit(i);i+=size;start=i;leading=separator
        else:i+=1
    emit(len(text))
    output=[];conditional=False;consequent=False;valid_conditional=False
    # Recognizable consequence establishes the bounded conditional scope. It does
    # not immunize later clauses. Sentences are separate scope domains.
    for index,(a,b,boundary) in enumerate(pieces):
        value=text[a:b].strip(' ,');low=value.lower();ambiguity=None
        if boundary=='SENTENCE':conditional=False;consequent=False;valid_conditional=False
        opening=bool(re.match(r'^(?:if|assuming|suppose|were)\b',low))
        if opening:
            conditional=True;consequent=False
            upcoming=[]
            for x,y,sep in pieces[index+1:]:
                if sep=='SENTENCE':break
                upcoming.append((text[x:y],sep))
            valid_conditional=any(MODAL.search(t) and sep in ('COMMA','then') for t,sep in upcoming)
        if conditional and not consequent and boundary in ('COMMA','then') and MODAL.search(value):consequent=True
        if re.match(r'^(?:i|we)\s+(?:(?:do not|don.t)\s+know\s+whether|think|believe|suspect|wonder)\b',low):
            kind='UNCERTAIN';scope='embedded question, no affirmative assertion';ambiguity='Whether-clause not an executed receipt'
        elif opening or conditional and not valid_conditional or conditional and not consequent and valid_conditional:
            kind='HYPOTHETICAL' if valid_conditional else 'UNKNOWN';scope='conditional antecedent' if valid_conditional else 'unresolved conditional'
            if not valid_conditional:ambiguity='No bounded conditional consequence established'
        elif conditional and consequent and MODAL.search(value):kind='HYPOTHETICAL';scope='explicit modal consequence/proposition'
        elif conditional and consequent and boundary in ('COMMA','then'):
            kind='UNKNOWN';scope='conditional consequence binding unclear';ambiguity='Unmodalized consequence may remain conditional'
        else:
            kind='ASSERTED_SUBORDINATE' if boundary in ('although','though','even though','whereas','because','since','while','despite','except') else 'ASSERTED'
            scope='local proposition; no inherited exemption'
        if boundary=='except' and AUTHORITY.search(value):kind='UNKNOWN';scope='exception to neighboring claim';ambiguity='Exception scope requires review'
        if kind=='HYPOTHETICAL' and consequent:
            residual=CONNECTORS.search(value)
            if residual and AUTHORITY.search(value[residual.end():]):
                kind='UNKNOWN';scope='unparsed embedded authority proposition';ambiguity='Modifier/coordination authority scope not safely partitioned'
            elif re.search(r'\b(?:i|we)\s+(?:ran|executed|tested|performed)\b|\b(?:tests?|checks?)\s+(?:had\s+)?passed\b|\bevidence\s+(?:confirms|confirmed|verified)\b',low):
                kind='UNKNOWN';scope='embedded tensed authority claim';ambiguity='Modal consequence does not establish scope of this embedded claim'
        polarity='NEGATIVE_OR_COMPLEX' if re.search(r'\b(?:not|no|never|without)\b',low) else 'POSITIVE_OR_UNSPECIFIED'
        if closing and AUTHORITY.search(value):kind='UNKNOWN';ambiguity='Unclosed quote';scope='unresolved quotation'
        output.append(ClauseAssessment(value,a,b,kind,polarity,scope,ambiguity))
    return output
