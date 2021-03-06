
from hu_entity.legacy_entity_finder import LegacyEntityFinder


def test_entity_finder_basic():
    finder = LegacyEntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.find_entity_values("I want a Carrot cake")
    assert(len(found_matches["Carrot"]) == 1)
    assert("CakeType" in found_matches["Carrot"])


def test_entity_finder_no_entities():
    finder = LegacyEntityFinder()
    values = {}
    finder.setup_entity_values(values)
    found_matches = finder.find_entity_values("I want a Carrot cake")
    assert(len(found_matches) == 0)


def test_entity_finder_no_matches():
    finder = LegacyEntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.find_entity_values("I want a cake")
    assert(len(found_matches) == 0)


def test_entity_finder_multiple_matches():
    finder = LegacyEntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.find_entity_values("I want a Carrot cake and then more carrot cake")
    assert(len(found_matches["Carrot"]) == 1)
    assert("CakeType" in found_matches["Carrot"])


def test_entity_finder_substring_matches():
    finder = LegacyEntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.find_entity_values("I want a Diet Coke")
    assert(len(found_matches) == 1)
    assert(len(found_matches["Diet Coke"]) == 1)
    assert("Drinks" in found_matches["Diet Coke"])


def test_entity_finder_duplicate_matches():
    finder = LegacyEntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.find_entity_values("I want a chocolate cake and a chocolate biscuit")
    assert(len(found_matches["chocolate"]) == 2)
    assert("CakeType" in found_matches["chocolate"])
    assert("Biscuit" in found_matches["chocolate"])


def test_entity_finder_multiple_value_matches():
    finder = LegacyEntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.find_entity_values("I want a Carrot cake and then a beer to drink")
    assert(len(found_matches["Carrot"]) == 1)
    assert("CakeType" in found_matches["Carrot"])
    assert(len(found_matches["beer"]) == 1)
    assert("Drinks" in found_matches["beer"])


def test_entity_finder_case_insensitive():
    finder = LegacyEntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.find_entity_values("I want a carrot cake")
    assert(len(found_matches["carrot"]) == 1)
    assert("CakeType" in found_matches["carrot"])


def test_entity_finder_ignore_punctuation():
    finder = LegacyEntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.find_entity_values("I want a cake, maybe carrot?")
    assert(len(found_matches["carrot"]) == 1)
    assert("CakeType" in found_matches["carrot"])


def test_entity_finder_multi_word_values():
    finder = LegacyEntityFinder()
    values = setup_data()
    finder.setup_entity_values(values)
    found_matches = finder.find_entity_values("I want some red wine and a cake")
    assert(len(found_matches["red wine"]) == 1)
    assert("Drinks" in found_matches["red wine"])


def test_entity_finder_regex():
    finder = LegacyEntityFinder()
    regex = setup_regex()
    finder.setup_regex_entities(regex)
    found_matches = finder.find_entity_values("I want a large cake")
    assert(len(found_matches)) == 2
    assert(len(found_matches["large"]) == 1)
    assert("CakeSizeRegex" in found_matches["large"])
    assert(len(found_matches["cake"]) == 1)
    assert("CakeTypeRegex" in found_matches["cake"])


def test_entity_finder_regex_and_standard():
    finder = LegacyEntityFinder()
    values = setup_data()
    regex = setup_regex()
    finder.setup_entity_values(values)
    finder.setup_regex_entities(regex)
    found_matches = finder.find_entity_values("I want a Large cake and some beer")
    assert(len(found_matches)) == 3

    # Note this test also ensures that a word is not
    assert(len(found_matches["Large"]) == 1)
    assert("CakeSize" in found_matches["Large"])
    assert(len(found_matches["beer"]) == 1)
    assert("Drinks" in found_matches["beer"])
    assert(len(found_matches["cake"]) == 1)
    assert("CakeTypeRegex" in found_matches["cake"])


def test_entity_finder_regex_single_word_only():
    finder = LegacyEntityFinder()
    regex = setup_regex()
    finder.setup_regex_entities(regex)
    found_matches = finder.find_entity_values("I want a Large biscuit")
    assert(len(found_matches)) == 1
    assert(len(found_matches["Large"]) == 1)
    assert("CakeSizeRegex" in found_matches["Large"])


def test_entity_finder_list_type_priority():
    finder = LegacyEntityFinder()
    values = setup_data()
    regex = setup_regex()
    finder.setup_entity_values(values)
    finder.setup_regex_entities(regex)
    found_matches = finder.find_entity_values("Large")
    assert(len(found_matches)) == 1
    assert(len(found_matches["Large"]) == 1)
    assert("CakeSize" in found_matches["Large"])


def test_entity_finder_split_message():
    finder = LegacyEntityFinder()
    words = finder.split_message("This is short")
    assert(len(words) == 6)


def setup_data():
    values = {"CakeSize": ["Large", "Medium", "Tiny"],
              "CakeType": ["Carrot", "Chocolate", "Coffee", "Sponge"],
              "Drinks": ["Coffee", "Beer", "Red Wine", "White Wine", "Coke", "Diet Coke"],
              "Biscuit": ["Rich Tea", "Digestive", "Chocolate"]}
    return values


def setup_regex():
    regex = {"CakeSizeRegex": "^[Ll].+$",
             "CakeTypeRegex": "^[Cc].+$"}
    return regex
