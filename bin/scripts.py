import path
import time
import os
import base64
import config
import lockfile

scheme = 'script'
extension = 'r'
uploaded_stanza_key = 'uploaded'


def get_custom_scripts_path():
    return path.get_directory('scripts')


def create_files(service):
    lock_file_path = path.get_file('scripts.lock')
    with lockfile.file_lock(lock_file_path):

        custom_scripts_path = get_custom_scripts_path()

        filenames = set()

        # check configuration for requred scripts
        for stanza, name in config.iter_stanzas(service, scheme):
            filename = name + os.path.extsep + extension
            full_path = os.path.join(custom_scripts_path, filename)

            # in case there is no uploaded attribute, add it with the current timestamp
            if not hasattr(stanza, uploaded_stanza_key):
                stanza = config.create_stanza(service, scheme, name, {
                    'content': stanza.__getattr__('content'),
                    uploaded_stanza_key: int(time.time())
                })

            if os.path.exists(full_path):
                # compare file creation date with stanza creation date
                modify_time = int(os.path.getmtime(full_path))
                uploaded_time = int(getattr(stanza, uploaded_stanza_key))
                if uploaded_time > modify_time:
                    os.remove(full_path)
                    create_file = True
                else:
                    create_file = False
            else:
                create_file = True

            if create_file:
                script_content = base64.decodestring(stanza.__getattr__('content'))
                with open(full_path, 'wb') as f:
                    f.write(script_content)

            filenames.add(filename)

        # remove files that are no longer in the list of configures scripts
        for filename in os.listdir(custom_scripts_path):
            if filename.endswith(os.path.extsep + extension):
                if not filename in filenames:
                    script_path = os.path.join(custom_scripts_path, filename)
                    os.remove(script_path)


def iter_stanzas(service):
    return config.iter_stanzas(service, scheme)


def get(service, script_name):
    for stanza, name in config.iter_stanzas(service, scheme):
        if name == script_name:
            return {
                'content': base64.decodestring(stanza.__getattr__('content')),
                'is_removable': stanza.access['removable'] == '1',
            }
    return None


def add(service, name, content):
    config.create_stanza(service, scheme, name, {
        'content': base64.encodestring(content).replace('\n', ''),
        uploaded_stanza_key: int(time.time())
    })


def remove(service, name):
    config.delete_stanza(service, scheme, name)