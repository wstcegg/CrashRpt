import xml.etree.ElementTree as ET
import json
import codecs
from collections import OrderedDict

tree = ET.parse('ModulesDefine.xml')
r = tree.getroot()


module_odict = OrderedDict()
for child in r:
    print(child.tag, child.attrib)

    info = child.attrib
    module = info['KEY']
    manager = info['VALUE']

    if manager == '':
        manager = "SWC"
    module_odict[module] = {"main": manager}

print(module_odict)

# # add exceptional rule
# od['ElementNewsFactory']['CElementGuBa'] = '刘旻'

clas_odict = OrderedDict()
clas_odict['CElementGuBa'] = '刘旻'

module_define_odict = {
    'module': module_odict,
    'class': clas_odict
}

jfile = codecs.open('ModulesDefine.json', 'w', 'utf-8')
json.dump(module_define_odict, jfile, ensure_ascii=False)
