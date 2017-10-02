from zope.interface import implementer
from sqlalchemy import (
    Column,
    String,
    Unicode,
    Integer,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)


from clld import interfaces
from clld.db.versioned import Versioned

from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from clld import interfaces
from clld.db.meta import Base, CustomModelMixin
#from clld.db.models.common import Language

from clld.db.models.common import (
    Language,
    Parameter,
    Contribution,
    Value,
)
from clld_glottologfamily_plugin.models import HasFamilyMixin


@implementer(interfaces.ILanguage)
class lsiLanguage(CustomModelMixin, Language, HasFamilyMixin):
    pk = Column(Integer, ForeignKey('language.pk'), primary_key=True)
    representation = Column(Integer)
    
@implementer(interfaces.IValue)
class lsiValue(CustomModelMixin, Value):
    pk = Column(Integer, ForeignKey('value.pk'), primary_key=True)
    comment = Column(Unicode)
    example = Column(Unicode)
    contributed_datapoint = Column(Unicode)


class FeatureDomain(Base, Versioned):
    name = Column(Unicode, unique=True)


@implementer(interfaces.IContribution)
class Designer(CustomModelMixin, Contribution, Versioned):
    """Contributions in NTS are designers. These comprise a set of
    features with corresponding values and a descriptive text.
    """
    pk = Column(Integer, ForeignKey('contribution.pk'), primary_key=True)
    domain = Column(Unicode)
    contributor = Column(Unicode)
    pdflink = Column(Unicode)
    citation = Column(Unicode)


@implementer(interfaces.IParameter)
class Feature(CustomModelMixin, Parameter, Versioned):
    """Parameters in NTS are called feature. They are always related to one Designer.
    """
    pk = Column(Integer, ForeignKey('parameter.pk'), primary_key=True)
    doc = Column(String)
    vdoc = Column(String)
    name_french = Column(String)
    clarification = Column(String)
    alternative_id = Column(String)
    representation = Column(Integer)
    featuredomain_pk = Column(Integer, ForeignKey('featuredomain.pk'))
    featuredomain = relationship(FeatureDomain, lazy='joined')
    designer_pk = Column(Integer, ForeignKey('designer.pk'))
    designer = relationship(Designer, lazy='joined', backref="features")
    dependson = Column(String)
    abbreviation = Column(String)
    sortkey_str = Column(String)
    sortkey_int = Column(Integer)
    jl_relevant_unit = Column(String)
    jl_function = Column(String)
    jl_formal_means = Column(String)
#-----------------------------------------------------------------------------
# specialized common mapper classes
#-----------------------------------------------------------------------------
#@implementer(interfaces.ILanguage)
#class lsiLanguage(CustomModelMixin, Language):
#    pk = Column(Integer, ForeignKey('language.pk'), primary_key=True)
