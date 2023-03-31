import fiftyone.operators as foo
import fiftyone.operators.types as types

class WatchImporter(foo.DynamicOperator):
    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.define_property("create_dataset", types.Boolean(), default=False)
        if ctx.params.get('create_dataset', False):
            inputs.define_property("dataset_name", types.String(), default='watches')
        inputs.define_property("mode", types.Enum([
            "clear_dataset_and_import",
            "add_sample_unless_exists",
            "add_all_samples",
            "just_clear_dataset"
        ]))
        inputs.define_property("img_dir", types.String())
        inputs.define_property("labels_path", types.String())
        labels_path = ctx.params.get('labels_path', None)
        if labels_path is not None:
            if exists(labels_path):
                try:
                    samples_to_import = len(load_json(labels_path))
                except:
                    samples_to_import = 0

                inputs.define_property("samples_to_import", types.Number(), default=samples_to_import)
            else:
                inputs.define_property("number_of_samples_imported", types.Number(), default=0)
        return inputs
    def execute(self, ctx):
        if ctx.params.get('create_dataset', False):
            ctx.dataset = fo.Dataset(name=ctx.params.get('dataset_name', 'watches'))
        img_dir = ctx.params.get('img_dir', '/Users/ritchie/fiftyone/watches')
        labels_path = ctx.params.get('labels_path', None)
        mode = ctx.params.get('mode', 'delete_dataset_and_import')
        if mode == 'clear_dataset_and_import' or mode == 'just_clear_dataset':
            ctx.dataset.clear()
            if mode == 'just_clear_dataset':
                return {
                    'number_of_samples_imported': 0
                }
        raw_labels = load_json(labels_path)
        parsed = iter_items(raw_labels, img_dir)
        ds = ctx.dataset
        samples = []
        for item in parsed:
            filepath = item.get('filepath', None)
            if (filepath is not None):
                samples.append(fo.Sample(filepath=filepath, **without_fp(item)))
        ds.add_samples(samples)
        return {
            'number_of_samples_imported': len(samples)
        }

        


op = None

def register():
    op = WatchImporter("watch_importer", "Import watches dataset")
    op.define_output_property("number_of_samples_imported", types.Number())
    foo.register_operator(op)
def unregister():
    foo.unregister_operator(op)

import json
import random
import re
import hashlib
import fiftyone as fo
from os.path import exists

# a function that loads a json file and returns a dictionary
def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

# a function that prints all the keys in a dictionary
def print_keys(data):
    print('Keys:')
    for key in data.keys():
        print(key)

# a function that selects a random subset of n objects in the given list
def random_subset(n, data):
    return random.sample(data, n)


# a function that prints a sampling of values for a given key
# and an array of dictionaries
def print_sample(key, data, n=5):
    print('Sample of {}:'.format(key))
    for item in random_subset(n, data):
        print(item.get(key, None))

# a function that takes a dictionary and a key in the dictionary referencing a sub dictionary
# and returns a flattened dictionary with the sub dictionary keys as top level keys
def flatten_dict(d, key):
    new_d = {}
    for k, v in d.items():
        if k != key:
           new_d[k] = v
    for k, v in d[key].items():
        new_d[k] = v
    return new_d

# a function that converts camel case strings to underscore separated strings
# it should handle cases like fooURLBar and fooURLBarBaz
def camel_to_underscore(s):
    s = s.replace('URL', 'Url')
    s = s.replace('ID', 'Id')
    return re.sub(r'(?<!^)(?=[A-Z])', '_', s).lower().replace(' ', '')

# a function that given a dictionary it returns a dictionary
# where the keys are normalized to be lowercase with underscores
# and parentheses removed
def normalize_keys(d):
    new_d = {}
    for k, v in d.items():
        k = camel_to_underscore(k)
        k = k.replace('(', '')
        k = k.replace(')', '')
        new_d[k] = v
    return new_d

# a function that removes keys from a dictionary where the value is None
def remove_none_values(d):
    new_d = {}
    for k, v in d.items():
        if v is not None and v != '':
            new_d[k] = v
    return new_d

# replaces the value for the given key in a dictionary
# where the value is a string of comma separated values
# with an array of those values
def split_comma_separated_values(d, key):
    new_d = {}
    for k, v in d.items():
        if k == key:
            new_d[k] = [s.strip() for s in v.split(',')]
        else:
            new_d[k] = v
    return new_d

# a function that removes the given key from a dictionary
def remove_key(d, key):
    new_d = {}
    for k, v in d.items():
        if k != key:
            new_d[k] = v
    return new_d

# a function that returns an md5 hash of the given string
def md5(s, id):
    if (s is None):
      print("FAILED TO HASH: " + id)
    return hashlib.md5(s.encode('utf-8')).hexdigest()

# a function that replaces a string at the given key
# with a number parsed from the string
def parse_int(d, key):
    new_d = {}
    for k, v in d.items():
        if k == key:
            new_d[k] = int(re.sub(r'\D', '', v))
        else:
            new_d[k] = v
    return new_d

def parse_float(d, key):
    new_d = {}
    for k, v in d.items():
        if k == key:
            new_d[k] = float(re.sub(r'\D', '', v))
        else:
            new_d[k] = v
    return new_d

def iter_items(data, img_dir):
    parsed = []
    for item in data:
        item = remove_none_values(item)
        item = flatten_dict(item, 'meta')
        item = normalize_keys(item)
        item = split_comma_separated_values(
          item, 'references'
        )
        item = split_comma_separated_values(
          item, 'complications'
        )
        item = split_comma_separated_values(
          item, 'features'
        )
        item['link'] = f'https://watchcharts.com{item.get("page_path")}'
        item = remove_key(item, 'page_path')
        item = parse_int(item, 'water_resistance')
        item = parse_int(item, 'case_diameter')
        item = parse_int(item, 'case_thickness')
        item = parse_int(item, 'numberof_jewels')
        item = parse_int(item, 'power_reserve')
        item = parse_int(item, 'lug_width')
        item = parse_int(item, 'frequency')
        main_image_url = item.get('main_image_url', None)
        if (main_image_url is None):
            print('WTF')
            print(item)
        else:
            item = remove_key(item, 'main_image_url')
            img_filename = md5(main_image_url, item.get('product_title', 'n/a')) + '.jpg'
            item['filepath'] = f'{img_dir}/{img_filename}'
        fp = item.get('filepath', None)
        if (fp is not None and exists(fp)):
            parsed.append(item)
            print_item(item)
    return parsed

def print_item(item):
    print('......................................')
    for k, v in item.items():
        print('{}: {}'.format(k, v))

def without_fp(d):
    new_d = {}
    for k, v in d.items():
        if k != 'filepath':
            new_d[k] = v
    return new_d


