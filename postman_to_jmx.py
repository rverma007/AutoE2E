import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

INPUT = r'D:\Downloads\New Collection.postman_collection (3).json'
OUTPUT = r'D:\Downloads\New_Collection.jmx'

with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

def get_all_requests(items, folder_name=''):
    reqs = []
    for item in items:
        if 'request' in item:
            reqs.append((folder_name, item))
        elif 'item' in item:
            reqs.extend(get_all_requests(item['item'], item.get('name', '')))
    return reqs

all_reqs = get_all_requests(data.get('item', []))
collection_name = data['info'].get('name', 'Collection')

def build_url(url_obj):
    if isinstance(url_obj, str):
        return url_obj
    return url_obj.get('raw', '')

def get_host_port_path(url_obj):
    if isinstance(url_obj, str):
        raw = url_obj
    else:
        raw = url_obj.get('raw', '')
    proto = 'https' if raw.startswith('https') else 'http'
    port = '443' if proto == 'https' else '80'
    stripped = raw.replace('https://', '').replace('http://', '')
    parts = stripped.split('/', 1)
    host = parts[0]
    path = '/' + parts[1] if len(parts) > 1 else '/'
    if ':' in host:
        host, port = host.split(':', 1)
    return proto, host, port, path

def build_jmx(collection_name, requests):
    jmx = ET.Element('jmeterTestPlan', version='1.2', properties='5.0', jmeter='5.6.3')
    hashtree_root = ET.SubElement(jmx, 'hashTree')

    tg_plan = ET.SubElement(hashtree_root, 'TestPlan',
        guiclass='TestPlanGui', testclass='TestPlan',
        testname=collection_name, enabled='true')
    ET.SubElement(tg_plan, 'stringProp', name='TestPlan.comments')
    ET.SubElement(tg_plan, 'boolProp', name='TestPlan.functional_mode').text = 'false'
    ET.SubElement(tg_plan, 'boolProp', name='TestPlan.serialize_threadgroups').text = 'false'
    uv = ET.SubElement(tg_plan, 'elementProp',
        name='TestPlan.user_defined_variables', elementType='Arguments',
        guiclass='ArgumentsPanel', testclass='Arguments',
        testname='User Defined Variables', enabled='true')
    ET.SubElement(uv, 'collectionProp', name='Arguments.arguments')
    ET.SubElement(tg_plan, 'stringProp', name='TestPlan.user_define_classpath')

    hashtree_plan = ET.SubElement(hashtree_root, 'hashTree')

    tg = ET.SubElement(hashtree_plan, 'ThreadGroup',
        guiclass='ThreadGroupGui', testclass='ThreadGroup',
        testname='Thread Group', enabled='true')
    ET.SubElement(tg, 'stringProp', name='ThreadGroup.on_sample_error').text = 'continue'
    loops = ET.SubElement(tg, 'elementProp',
        name='ThreadGroup.main_controller', elementType='LoopController',
        guiclass='LoopControlPanel', testclass='LoopController',
        testname='Loop Controller', enabled='true')
    ET.SubElement(loops, 'boolProp', name='LoopController.continue_forever').text = 'false'
    ET.SubElement(loops, 'stringProp', name='LoopController.loops').text = '1'
    ET.SubElement(tg, 'stringProp', name='ThreadGroup.num_threads').text = '1'
    ET.SubElement(tg, 'stringProp', name='ThreadGroup.ramp_time').text = '1'
    ET.SubElement(tg, 'boolProp', name='ThreadGroup.scheduler').text = 'false'
    ET.SubElement(tg, 'stringProp', name='ThreadGroup.duration')
    ET.SubElement(tg, 'stringProp', name='ThreadGroup.delay')

    hashtree_tg = ET.SubElement(hashtree_plan, 'hashTree')

    for idx, (folder, item) in enumerate(requests):
        req = item['request']
        name = item.get('name', f'Request {idx+1}')
        method = req.get('method', 'GET')
        url_obj = req.get('url', '')
        proto, host, port, path = get_host_port_path(url_obj)

        params = []
        if isinstance(url_obj, dict):
            params = url_obj.get('query', []) or []

        sampler = ET.SubElement(hashtree_tg, 'HTTPSamplerProxy',
            guiclass='HttpTestSampleGui', testclass='HTTPSamplerProxy',
            testname=name, enabled='true')

        args_elem = ET.SubElement(sampler, 'elementProp',
            name='HTTPsampler.Arguments', elementType='Arguments',
            guiclass='HTTPArgumentsPanel', testclass='Arguments',
            testname='User Defined Variables', enabled='true')
        args_coll = ET.SubElement(args_elem, 'collectionProp', name='Arguments.arguments')

        body = req.get('body') or {}
        mode = body.get('mode', '')

        if mode == 'raw':
            raw_body = body.get('raw', '')
            ET.SubElement(sampler, 'boolProp', name='HTTPSampler.postBodyRaw').text = 'true'
            arg = ET.SubElement(args_coll, 'elementProp', name='', elementType='HTTPArgument')
            ET.SubElement(arg, 'boolProp', name='HTTPArgument.always_encode').text = 'false'
            ET.SubElement(arg, 'stringProp', name='Argument.value').text = raw_body
            ET.SubElement(arg, 'stringProp', name='Argument.metadata').text = '='
        elif mode == 'formdata':
            ET.SubElement(sampler, 'boolProp', name='HTTPSampler.postBodyRaw').text = 'false'
            for fd in body.get('formdata', []):
                arg = ET.SubElement(args_coll, 'elementProp',
                    name=fd.get('key', ''), elementType='HTTPArgument')
                ET.SubElement(arg, 'boolProp', name='HTTPArgument.always_encode').text = 'false'
                ET.SubElement(arg, 'stringProp', name='Argument.name').text = fd.get('key', '')
                ET.SubElement(arg, 'stringProp', name='Argument.value').text = fd.get('value', '')
                ET.SubElement(arg, 'stringProp', name='Argument.metadata').text = '='
                ET.SubElement(arg, 'boolProp', name='HTTPArgument.use_equals').text = 'true'
        else:
            ET.SubElement(sampler, 'boolProp', name='HTTPSampler.postBodyRaw').text = 'false'
            for p in params:
                arg = ET.SubElement(args_coll, 'elementProp',
                    name=p.get('key', ''), elementType='HTTPArgument')
                ET.SubElement(arg, 'boolProp', name='HTTPArgument.always_encode').text = 'false'
                ET.SubElement(arg, 'stringProp', name='Argument.name').text = p.get('key', '')
                ET.SubElement(arg, 'stringProp', name='Argument.value').text = p.get('value', '')
                ET.SubElement(arg, 'stringProp', name='Argument.metadata').text = '='
                ET.SubElement(arg, 'boolProp', name='HTTPArgument.use_equals').text = 'true'

        ET.SubElement(sampler, 'stringProp', name='HTTPSampler.domain').text = host
        ET.SubElement(sampler, 'stringProp', name='HTTPSampler.port').text = port
        ET.SubElement(sampler, 'stringProp', name='HTTPSampler.protocol').text = proto
        path_no_qs = path.split('?')[0]
        ET.SubElement(sampler, 'stringProp', name='HTTPSampler.path').text = path_no_qs
        ET.SubElement(sampler, 'stringProp', name='HTTPSampler.method').text = method
        ET.SubElement(sampler, 'boolProp', name='HTTPSampler.follow_redirects').text = 'true'
        ET.SubElement(sampler, 'boolProp', name='HTTPSampler.auto_redirects').text = 'false'
        ET.SubElement(sampler, 'boolProp', name='HTTPSampler.use_keepalive').text = 'true'
        ET.SubElement(sampler, 'boolProp', name='HTTPSampler.DO_MULTIPART_POST').text = 'true' if mode == 'formdata' else 'false'
        ET.SubElement(sampler, 'stringProp', name='HTTPSampler.embedded_url_re')
        ET.SubElement(sampler, 'stringProp', name='HTTPSampler.connect_timeout')
        ET.SubElement(sampler, 'stringProp', name='HTTPSampler.response_timeout')

        # Headers
        headers = req.get('header', [])
        active_headers = [h for h in headers if not h.get('disabled')]
        if active_headers:
            hm = ET.SubElement(hashtree_tg, 'HeaderManager',
                guiclass='HeaderPanel', testclass='HeaderManager',
                testname=f'{name} - Headers', enabled='true')
            hm_coll = ET.SubElement(hm, 'collectionProp', name='HeaderManager.headers')
            for h in active_headers:
                he = ET.SubElement(hm_coll, 'elementProp', name='', elementType='Header')
                ET.SubElement(he, 'stringProp', name='Header.name').text = h.get('key', '')
                ET.SubElement(he, 'stringProp', name='Header.value').text = h.get('value', '')
            ET.SubElement(hashtree_tg, 'hashTree')

        ET.SubElement(hashtree_tg, 'hashTree')

    # Result collector (View Results Tree)
    rc = ET.SubElement(hashtree_plan, 'ResultCollector',
        guiclass='ViewResultsFullVisualizer', testclass='ResultCollector',
        testname='View Results Tree', enabled='true')
    ET.SubElement(rc, 'boolProp', name='ResultCollector.error_logging').text = 'false'
    objprop = ET.SubElement(rc, 'objProp')
    ET.SubElement(objprop, 'name').text = 'saveConfig'
    value = ET.SubElement(objprop, 'value', **{'class': 'SampleSaveConfiguration'})
    ET.SubElement(value, 'time').text = 'true'
    ET.SubElement(value, 'latency').text = 'true'
    ET.SubElement(value, 'timestamp').text = 'true'
    ET.SubElement(value, 'success').text = 'true'
    ET.SubElement(value, 'label').text = 'true'
    ET.SubElement(value, 'code').text = 'true'
    ET.SubElement(value, 'message').text = 'true'
    ET.SubElement(value, 'threadName').text = 'true'
    ET.SubElement(value, 'dataType').text = 'true'
    ET.SubElement(value, 'encoding').text = 'false'
    ET.SubElement(value, 'assertions').text = 'true'
    ET.SubElement(value, 'subresults').text = 'true'
    ET.SubElement(value, 'responseData').text = 'false'
    ET.SubElement(value, 'samplerData').text = 'false'
    ET.SubElement(value, 'xml').text = 'false'
    ET.SubElement(value, 'fieldNames').text = 'true'
    ET.SubElement(value, 'responseHeaders').text = 'false'
    ET.SubElement(value, 'requestHeaders').text = 'false'
    ET.SubElement(value, 'responseDataOnError').text = 'false'
    ET.SubElement(value, 'saveAssertionResultsFailureMessage').text = 'true'
    ET.SubElement(value, 'bytes').text = 'true'
    ET.SubElement(value, 'sentBytes').text = 'true'
    ET.SubElement(value, 'url').text = 'true'
    ET.SubElement(value, 'threadCounts').text = 'true'
    ET.SubElement(value, 'idleTime').text = 'true'
    ET.SubElement(value, 'connectTime').text = 'true'
    ET.SubElement(rc, 'stringProp', name='filename')
    ET.SubElement(hashtree_plan, 'hashTree')

    return jmx

jmx = build_jmx(collection_name, all_reqs)
xml_str = ET.tostring(jmx, encoding='unicode')
dom = minidom.parseString(xml_str)
pretty = dom.toprettyxml(indent='  ', encoding='UTF-8').decode('utf-8')
pretty = pretty.replace(
    '<?xml version="1.0" ?>',
    '<?xml version="1.0" encoding="UTF-8"?>'
)

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(pretty)

print(f'Done! Saved to: {OUTPUT}')
print(f'Total requests converted: {len(all_reqs)}')
