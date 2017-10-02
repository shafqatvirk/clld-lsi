from __future__ import unicode_literals
import sys
from itertools import groupby
from collections import Counter
import csv
from functools import partial
import io
from datetime import date, datetime
import os
import itertools

import transaction
from pytz import utc

from clld.scripts.util import initializedb, Data, gbs_func, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.db.util import compute_language_sources
from clld.lib.bibtex import unescape, Record
from dsv import reader
from clld_glottologfamily_plugin.util import load_families


import issues

import lsi
from lsi import models
from lsi import util
from clldclient.glottolog import Glottolog
##from clld.web import icon

import issues
NOCODE_TO_GLOTTOCODE = {
    'NOCODE_Apolista': 'apol1242',
    'NOCODE_Maipure': 'maip1246',
    'NOCODE_Ngala-Santandrea': 'ngal1296',
    'NOCODE_Nzadi': 'nzad1234',
    'NOCODE_Paunaca': 'paun1241',
    'NOCODE_Sisiqa': 'sisi1250',
}


def savu(txt, fn):
    with io.open(fn, 'w', encoding="utf-8") as fp:
        fp.write(txt)


def ktfbib(s):
    rs = [z.split(":::") for z in s.split("|||")]
    [k, typ] = rs[0]
    return k, (typ, dict(rs[1:]))


def _dtab(dir_, fn):
    ##print fn,dir_
    lpd = []
    #for d in reader(dir_.joinpath(fn), dicts=True, quoting=csv.QUOTE_NONE):
    for d in reader(('/Users/virk/shafqat/postDoc-Swe/project/clld/clld/lsi/lsi/data/'+fn), dicts=True, quoting=csv.QUOTE_NONE):
        lpd.append({
            k.replace('\ufeff', ''): (v or '').strip()
            for k, v in d.items() + [("fromfile", fn)]})
    return lpd


def grp2(l):
    return [
        (k, [_i[1] for _i in i]) for k, i in
        groupby(sorted((a, b) for a, b in l), key=lambda t: t[0])]


def mergeds(ds):
    """Merge a list of dictionaries by aggregating keys and taking the longest value for
    each key.
    :param ds: an iterable of dictionaries
    :return: the merged dictionary.
    """
    return {k: vs.next()[1] for k, vs in groupby(sorted(
        [(k, v) for d in ds for (k, v) in d.items()],
        key=lambda t: (t[0], len(t[1])),
        reverse=True),
        key=lambda t: t[0])}


def longest(ss):
    return max([(len(s), s) for s in ss])[1]


def dp_dict(ld):
    assert 'language_id' in ld and ld.get('feature_alphanumid')
    return {
        k: v.replace(".", "-") if k in ['feature_alphanumid', 'value'] else v
        for (k, v) in ld.iteritems()}

def main(args):
    data = Data(
        created=utc.localize(datetime(2013, 11, 15)),
        updated=utc.localize(datetime(2013, 12, 12)))
    icons = issues.Icons()
    #print icons

    DBSession.execute("delete from Language")
    DBSession.execute("delete from Unit")
    DBSession.execute("delete from featuredomain")
    DBSession.execute("delete from family")
    DBSession.execute("delete from source")
    DBSession.execute("delete from parameter")
    DBSession.execute("delete from feature")
    DBSession.execute("delete from domainelement")
    DBSession.execute("delete from valueset")
    DBSession.execute("delete from value")
    DBSession.execute("delete from lsivalue")
    DBSession.execute("delete from dataset")
    DBSession.execute("delete from contributor")
    DBSession.execute("delete from lsilanguage")
    DBSession.execute("delete from contribution")
    DBSession.execute("delete from designer")
    
    
    
    
    DBSession.flush()
    
    dtab = partial(_dtab, args.data_file())

    #Languages
    
    #print args.data_file()
    #tabfns = ['%s' % fn.basename() for fn in args.data_file().files('nts_*.tab')]
    #tabfns = ['nts_18.tab']
    tabfns = os.listdir('/Users/virk/shafqat/postDoc-Swe/project/clld/clld/lsi/lsi/data')[1:]
    #print tabfns
    args.log.info("Sheets found: %s" % tabfns)
    ldps = []
    lgs = {}
    nfeatures = Counter()
    nlgs = Counter()

    for fn in tabfns:
        for ld in dtab(fn):
            
            if ld['language_id'] == 'qgr':
                continue
            if "feature_alphanumid" not in ld:
                args.log.info("NO FEATUREID %s %s" % (len(ld), ld))
            if not ld["feature_alphanumid"].startswith("DRS") \
                    and ld["feature_alphanumid"].find(".") == -1:
                ldps.append(dp_dict(ld))
                ##print ld
                lgs[ld['language_id']] = unescape(ld['language_name'])
                if ld["value"] != "?":
                    nfeatures.update([ld['language_id']])
                    nlgs.update([ld['feature_alphanumid']])

    ldps = sorted(ldps, key=lambda d: d['feature_alphanumid'])

    #lgs["ygr"] = "Hua"

    for lgid, lgname in lgs.items():
        data.add(
            models.lsiLanguage, lgid,
            id=lgid,
            name=lgname,
            representation=nfeatures.get(lgid, 0))
    DBSession.flush()
    #print "I am here"
    #print data['ntsLanguage'].values()[1].id
    load_families(
        data,
        [(NOCODE_TO_GLOTTOCODE.get(l.id, l.id), l) for l in data['lsiLanguage'].values()],
        isolates_icon='tcccccc')
    #print 'family'
    #print data['Family'].get('sino1245').jsondata
    #Domains
    for domain in set(ld['feature_domain'] for ld in ldps):
        data.add(models.FeatureDomain, domain, name=domain)
    DBSession.flush()

    #Designers
    #for i, info in enumerate(dtab("ntscontributions.tab") + dtab("ntscontacts.tab")):
    for i, info in enumerate([{'designer':'shafqat','domain':'','pdflink':'','citation':''},{'designer':'-','domain':'','pdflink':'','citation':''}]):
        designer_id = str(i + 1)
        data.add(
            models.Designer, info['designer'],
            id=designer_id,
            name=designer_id,
            domain=info["domain"],
            contributor=info['designer'],
            pdflink=info["pdflink"],
            citation=info["citation"])
    DBSession.flush()

    #Sources
    '''for k, (typ, bibdata) in [
        ktfbib(bibsource) for ld in ldps
        if ld.get(u'bibsources') for bibsource in ld['bibsources'].split(",,,")
    ]:
        if k not in data["Source"]:
            data.add(common.Source, k, _obj=bibtex2source(Record(typ, k, **bibdata)))
    DBSession.flush()'''

    #Features
    fs = [(fid, mergeds(lds)) for fid, lds in
          groupby(ldps, key=lambda d: d['feature_alphanumid'])]

    fvdesc = [(fid, [(ld.get("feature_possible_values"), ld.get("fromfile")) for ld in lds if ld.get("feature_possible_values")]) for fid, lds in groupby(ldps, key=lambda d: d['feature_alphanumid'])]
    fvdt = [(fid, grp2(vdescs)) for (fid, vdescs) in fvdesc]
    fvmis = [(fid, vdescs) for (fid, vdescs) in fvdt if len(vdescs) > 1]
    

    for _, dfsids in groupby(
            sorted((f.get('feature_name', fid), fid) for fid, f in fs),
            key=lambda t: t[0]):
        assert len(list(dfsids)) == 1
    #print 'here is nlgs'
    
    for fid, f in fs:
        #print "lang name"
        #print ldps
        #print f.get('feature_possible_values', ""),
        if not fid.isdigit():
            args.log.info("NO INT FID %s" % f)           
        feature = data.add(
            models.Feature, fid,
            id=fid,
            name=f.get('feature_name', f['feature_alphanumid']),
            doc=f.get('feature_information', ""),
            vdoc=f.get('feature_possible_values', ""),
            representation=nlgs.get(fid, 0),
            designer=data["Designer"][f['designer']],
            dependson=f.get("depends_on", ""),
            abbreviation=f.get("abbreviation", ""),
            featuredomain=data['FeatureDomain'][f["feature_domain"]],
            name_french=f.get('francais', ""),
            clarification=f.get("draft of clarifying comments to outsiders (hedvig + dunn + harald + suzanne)", ""),
            alternative_id=f.get("old feature number", ""),
            jl_relevant_unit=f.get("relevant unit(s)", ""),
            jl_function=f.get("function", ""),
            jl_formal_means=f.get("formal means", ""),
            sortkey_str="",
            sortkey_int=int(fid))

        vdesclist = [veq.split("==") for veq in feature.vdoc.split("||")]
        vdesc = {v.replace(".", "-"): desc for [v, desc] in vdesclist}
        ##vdesc = {v.replace(".", "-")+'-'+fmly: desc for ((v,desc),fmly) in itertools.product([(vv,desc) for [vv, desc] in vdesclist],['Austroasiatic','Dravidian','Indo-European','Sino-Tibetan'])}

        vdesc.setdefault('?', 'Not known')
        if 'N/A' not in vdesc and feature.dependson:
            vdesc["N/A"] = "Not Applicable"
        vi = {v: i for (i, v) in enumerate(sorted(vdesc.keys()))}
        ##vicons = {v+'-'+f:v+'-'+f for (v,f) in itertools.product(['0','1','2','3'],['Austroasiatic','Dravidian','Indo-European','Sino-Tibetan'])}
        ##vicons['?'] = 'c000000'
        ##vicons['N/A'] = 'c000000'
        vicons = icons.iconize(vi.keys())
        for v, desc in vdesc.items():
            #print v,vicons[v]
            data.add(
                common.DomainElement, (fid, v),
                id='%s-%s' % (fid, v),
                name=v,
                description=desc,
                jsondata={"icon": vicons[v]},
                number=vi[v],
                parameter=feature)
    DBSession.flush()

    for ((f, lg), ixs) in grp2(
            [((ld['feature_alphanumid'], ld['language_id']), i)
             for i, ld in enumerate(ldps)]):
        ixvs = set([ldps[ix]['value'] for ix in ixs])
        if len(ixvs) == 1:
            continue
        args.log.warn(
            "Dup value %s %s %s" %
            (f, lg, [(ldps[ix]['value'], ldps[ix]['fromfile']) for ix in ixs]))
        ##print "Dup value %s %s %s" % (f, lg, [(ldps[ix]['value'], ldps[ix]['fromfile'], ldps[ix].get('provenance')) for ix in ixs])
    errors = {}
    done = set()
    glottolog = Glottolog()
    for ld in ldps:
        
        '''############################### for printing different map markers for different familys for features:shafqat
        #print data['Family']
        
        language = data['lsiLanguage'][ld['language_id']]
        if isinstance(language, (tuple, list)) and len(language) == 2:
            code, language = language
        else:
            code = language.id
        if code != '-':
            gl_language = glottolog.languoid(code)
            if gl_language:
                gl_family = gl_language.family
                if gl_family:
                    family = data['Family'].get(gl_family.id)
                    
        ld['value'] = ld['value']+'-'+str(family)
        ##ld['value'] = combineValueFamily(ld['value'],str(family))
        #print family
        #####################################'''
        parameter = data['Feature'][ld['feature_alphanumid']]
        language = data['lsiLanguage'][ld['language_id']]
        
        id_ = '%s-%s' % (parameter.id, language.id)
        if id_ in done:
            continue

        if (ld['feature_alphanumid'], ld['value']) not in data['DomainElement']:
            if not ld["value"].strip():
                continue
            info = (
                ld['feature_alphanumid'],
                ld.get('feature_name', "[Feature Name Lacking]"),
                ld['language_id'],
                ld['value'],
                ld['fromfile'])
            msg = u"%s %s %s %s %s not in the set of legal values ({0})" % info
            args.log.error(msg.format(sorted(
                [y for (x, y) in data['DomainElement'].keys()
                 if x == ld['feature_alphanumid']])))
            ##print msg.format(sorted(
              ##  [y for (x, y) in data['DomainElement'].keys()
                ## if x == ld['feature_alphanumid']]))
            errors[(ld['feature_alphanumid'], ld['language_id'])] = info
            continue

        vs = common.ValueSet(
            id=id_,
            language=language,
            parameter=parameter,
            source=ld["source"] or None,
            ##contribution=parameter.designer
            )
        #print
        #print "this one"
        #print data['DomainElement'][(ld['feature_alphanumid'], ld['value'])].jsondata
        models.lsiValue(
            id=id_,
            domainelement=data['DomainElement'][(ld['feature_alphanumid'], ld['value'])],
            jsondata={"icon": data['DomainElement'][(ld['feature_alphanumid'], ld['value'])].jsondata},
            comment=ld["comment"],
            valueset=vs,
            contributed_datapoint=ld["contributor"])
        done.add(id_)

        '''if not ld.get('bibsources'):
            if 'bibsources' not in ld:
                args.log.warn("no bibsource %s" % ld)
            continue
        for k, _ in [ktfbib(bibsource) for bibsource in ld['bibsources'].split(",,,")]:
            common.ValueSetReference(valueset=vs, source=data['Source'][k])'''
    DBSession.flush()

    #To CLDF
    cldf = {}
    for ld in ldps:
        parameter = data['Feature'][ld['feature_alphanumid']]
        language = data['lsiLanguage'][ld['language_id']]
        id_ = '%s-%s' % (parameter.id, language.id)
        if not id_ in done:
            continue
        dt = (lgs[ld['language_id']], ld['language_id'], ld['feature_alphanumid'] + ". " + ld['feature_name'], ld["value"])
        cldf[dt] = None

    tab = lambda rows: u''.join([u'\t'.join(row) + u"\n" for row in rows])
    savu(tab([("Language", "iso-639-3", "Feature", "Value")] + cldf.keys()), "lsi.cldf")
        
    args.log.info('%s Errors' % len(errors))

    dataset = common.Dataset(
        id="LSI",
        name='Linguistic Survey of India',
        publisher_name="Sprakbanken",
        publisher_place="Gothenburg",
        publisher_url="to be given",
        description="this is to be followed",
        domain='http://lsi.clld.org',
        published=date(2016, 05, 16),
        contact='virk.shafqat@gmail.com',
        license='http://creativecommons.org/licenses/by-nc-nd/2.0/de/deed.en',
        jsondata={
            'license_icon': 'http://wals.info/static/images/cc_by_nc_nd.png',
            'license_name': 'Creative Commons Attribution-NonCommercial-NoDerivs 2.0 Germany'})

    # disabled for experimental purposes, names were appearing multiple times
    for i, contributor in enumerate([
        common.Contributor(
            id="Lars Borin",
            name="Lars Borin",
            email="lars.borin@svenska.gu.se"),
        common.Contributor(
            id="Shafqat Mumtaz Virk",
            name="Shafqat Mumtaz Virk",
            email="virk.shafqat@gmail.com"),
        common.Contributor(
            id="Anju Saxena",
            name="Anju Saxena",
            email="anju.saxena@lingfil.uu.se"),
        common.Contributor(
            id="Harald Hammarstrom",
            name="Harald Hammarstrom",
            email="harald.hammarstroem@mpi.nl")
        
        
           ]):
        #print i
        common.Editor(dataset=dataset, contributor=contributor, ord=i)
    
    '''cont1 = common.Contributor(
            id="Harald Hammarstrom",
            name="Harald Hammarstrom",
            email="harald.hammarstroem@mpi.nl")
    cont2= common.Contributor(
            id="Shafqat Mumtaz Virk",
            name="Shafqat Mumtaz Virk",
            email="virk.shafqat@gmail.com")
    cont3 = common.Contributor(
            id="Lars Borin",
            name="Lars Borin",
            email="lars.borin@svenska.gu.se")
    for contributor in [cont1,cont2,cont3]:
        common.Editor(dataset=dataset, contributor=contributor,ord=1)'''
    
    DBSession.add(dataset)
    DBSession.flush()
    
    #ctbs = DBSession.execute("select * from parameter where parameter.pk = 2").fetchall()
    #print ctbs
    
    
'''def combineValueFamily(value,family):
    if value == '0' and family == 'Austroasiatic':
        return 'c000000'
    elif value == '1' and family == 'Austroasiatic':
        return 'c0000dd'
    elif value == '2' and family == 'Austroasiatic':
        return 'c0000ff'
    elif value == '3' and family == 'Austroasiatic':
        return 'c009900'
    if value == '0' and family == 'Dravidian':
        return 'd000000'
    elif value == '1' and family == 'Dravidian':
        return 'd0000dd'
    elif value == '2' and family == 'Dravidian':
        return 'd0000ff'
    elif value == '3' and family == 'Dravidian':
        return 'd009900'
    if value == '0' and family == 'Indo-European':
        return 'f000000'
    elif value == '1' and family == 'Indo-European':
        return 'f0000dd'
    elif value == '2' and family == 'Indo-European':
        return 'f0000ff'
    elif value == '3' and family == 'Indo-European':
        return 'f009900'
    if value == '0' and family == 'Sino-Tibetan':
        return 't000000'
    elif value == '1' and family == 'Sino-Tibetan':
        return 't0000dd'
    elif value == '2' and family == 'Sino-Tibetan':
        return 't0000ff'
    elif value == '3' and family == 'Sino-Tibetan':
        return 't009900'
    else:
        return 'c00ffff'
    
def val2icon(v):
    if v=='0':
        return '000000'
    elif v=='1':
        return '0000dd'
    elif v=='2':
        return '0000ff'
    elif v=='3':
        return '009900' '''


def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodiucally whenever data has been updated.
    """


if __name__ == '__main__':
    initializedb(create=main, prime_cache=prime_cache)
    sys.exit(0)
