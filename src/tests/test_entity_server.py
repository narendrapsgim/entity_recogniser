# flake8: noqa
import pytest
from aiohttp import web
import hu_entity.server


@pytest.fixture(scope="module")
def ner_server():
    """EntityRecognizerServer takes ages to initialize, so define a single EntityRecognizerServer
    which will be reused in every test"""
    server = hu_entity.server.EntityRecognizerServer(minimal_ers_mode=True)
    server.initialize()
    return server


@pytest.fixture()
async def cli(loop, aiohttp_client, ner_server):
    """Defines the CLI test HTTP client which will start a test HTTP server.
    Will reuse the module level ner_server pytest fixture which is the slow bit to initialize"""
    web_app = web.Application()
    hu_entity.server.initialize_web_app(web_app, ner_server)
    return await aiohttp_client(web_app)


async def test_server_root_404(cli):
    resp = await cli.get('/')
    assert resp.status == 404


async def test_server_ner_no_q_400(cli):
    resp = await cli.get('/ner')
    assert resp.status == 400


async def test_server_ner_q_1(cli):
    resp = await cli.get('/ner?q=London')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 1
    item = json_resp[0]
    assert item['category'] == "sys.places"
    assert item['value'] == "London"
    assert item['start'] == 0
    assert item['end'] == 6


async def test_server_ner_no_entity(cli):
    resp = await cli.get('/ner?q=Nothing')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 0


async def test_server_ner_multi_instance(cli):
    resp = await cli.get('/ner?q=What weather is it in London tomorrow')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 2
    item = json_resp[0]
    assert item['category'] == "sys.places"
    assert item['value'] == "London"
    assert item['start'] == 22
    assert item['end'] == 28
    item = json_resp[1]
    assert item['category'] == "sys.date"
    assert item['value'] == "tomorrow"
    assert item['start'] == 29
    assert item['end'] == 37


async def test_server_ner_two_word_places(cli):
    resp = await cli.get('/ner?q=Whats the weather in New York')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 1
    item = json_resp[0]
    assert item['category'] == "sys.places"
    assert item['value'] == "New York"


async def test_server_tokenize(cli):
    resp = await cli.get('/tokenize?q=hi')
    assert resp.status == 200
    json_resp = await resp.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 1
    assert json_resp[0] == "hi"


async def test_server_find_entities_requires_body(cli):
    resp = await cli.post('/findentities')
    assert resp.status == 400


async def test_server_find_entities(cli):
    resp = await cli.post('/findentities', data='{"conversation" : "a Focus is a type of car, an Apple is a fruit","entities" : { "cars" : [ "Fiesta", "Focus", "Golf" ], "fruits" : [ "Apple", "Banana", "Pear" ] } }')
    assert resp.status == 200
    json_resp = await resp.json()
    assert json_resp['conversation'] == "a Focus is a type of car, an Apple is a fruit"
    values = json_resp['entities']
    assert next(iter(values['Focus'])) == "cars"
    assert next(iter(values['Apple'])) == "fruits"
    assert len(values) == 2

async def test_server_find_regex_entities(cli):
    resp = await cli.post('/findentities', data='{"conversation" : "Alarm number A213", "entities" : { "alarms" : [ "a210", "a211", "a212" ] }, "regex_entities" : { "ralarms" : "[A]\\\\d{3}$" } }')
    assert resp.status == 200
    json_resp = await resp.json()
    assert json_resp['conversation'] == "Alarm number A213"
    values = json_resp['entities']
    matched_entities=values['A213']
    assert len(matched_entities) == 1
    assert "ralarms" in matched_entities

async def test_server_find_regex_entities_value_priority(cli):
    resp = await cli.post('/findentities', data='{"conversation" : "Alarm number A212", "entities" : { "alarms" : [ "a210", "a211", "a212" ] }, "regex_entities" : { "ralarms" : "[A]\\\\d{3}$" } }')
    assert resp.status == 200
    json_resp = await resp.json()
    assert json_resp['conversation'] == "Alarm number A212"
    values = json_resp['entities']
    matched_entities=values['A212']
    assert len(matched_entities) == 1
    assert "alarms" in matched_entities

async def test_server_find_regex_only(cli):
    resp = await cli.post('/findentities', data='{"conversation" : "Alarm number A212", "entities" : { }, "regex_entities" : { "ralarms" : "[A]\\\\d{3}$" } }')
    assert resp.status == 200
    json_resp = await resp.json()
    assert json_resp['conversation'] == "Alarm number A212"
    values = json_resp['entities']
    assert next(iter(values['A212'])) == "ralarms"
    assert len(values) == 1

async def test_server_find_regex_only_case_sensitive(cli):
    resp = await cli.post('/findentities', data='{"conversation" : "Alarm number A212", "entities" : { }, "regex_entities" : { "ralarms" : "[a]\\\\d{3}$" } }')
    assert resp.status == 200
    json_resp = await resp.json()
    assert json_resp['conversation'] == "Alarm number A212"
    values = json_resp['entities']
    assert len(values) == 0

async def test_server_find_standard_only(cli):
    resp = await cli.post('/findentities', data='{"conversation" : "Alarm number A212", "entities" : { "alarms" : [ "A210", "A211", "A212" ] }, "regex_entities" : { } }')
    assert resp.status == 200
    json_resp = await resp.json()
    assert json_resp['conversation'] == "Alarm number A212"
    values = json_resp['entities']
    assert next(iter(values['A212'])) == "alarms"
    assert len(values) == 1

async def test_server_bad_regex(cli):
    resp = await cli.post('/findentities', data='{"conversation" : "Alarm number A212", "entities" : { "alarms" : [ "a210", "a211", "a212" ] }, "regex_entities" : { "ralarms" : "[a\\\\d{3}$" } }')
    assert resp.status == 400
    assert resp.reason == "Invalid regex found"

async def test_server_find_cached_entities(cli):
    resp = await cli.post('/v2/populate_entities', data='{"entities" : { "cars" : [ "Fiesta", "Focus", "Golf" ], "fruits" : [ "Apple", "Banana", "Pear" ] } }')
    assert resp.status == 200

    resp = await cli.post('/v2/entity_check', data='{"conversation" : "a Focus is a type of car, an Apple is a fruit"}')
    json_resp = await resp.json()

    assert json_resp['conversation'] == "a Focus is a type of car, an Apple is a fruit"
    values = json_resp['entities']
    assert next(iter(values['Focus'])) == "cars"
    assert next(iter(values['Apple'])) == "fruits"
    assert len(values) == 2

async def test_server_delete_entities(cli):
    resp = await cli.post('/v2/populate_entities', data='{"entities" : { "cars" : [ "Fiesta", "Focus", "Golf" ], "fruits" : [ "Apple", "Banana", "Pear" ] } }')
    assert resp.status == 200

    resp = await cli.post('/v2/entity_check', data='{"conversation" : "a Focus is a type of car, an Apple is a fruit"}')
    json_resp = await resp.json()
    
    assert json_resp['conversation'] == "a Focus is a type of car, an Apple is a fruit"
    values = json_resp['entities']
    assert next(iter(values['Focus'])) == "cars"
    assert next(iter(values['Apple'])) == "fruits"
    assert len(values) == 2

    resp = await cli.post('/v2/delete_entities', data='{"entities" : { "cars" : [ ] } }')
    assert resp.status == 200

    resp = await cli.post('/v2/entity_check', data='{"conversation" : "a Focus is a type of car, an Apple is a fruit"}')
    json_resp = await resp.json()

    assert json_resp['conversation'] == "a Focus is a type of car, an Apple is a fruit"
    values = json_resp['entities']
    assert len(values) == 1
    assert next(iter(values['Apple'])) == "fruits"
