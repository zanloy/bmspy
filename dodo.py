import docker
from version import __version__

name = 'bmspy'
image_name = f'{name}:{__version__}'
repo = 'container-registry.dev8.bip.va.gov/bms/bmspy'

def task_build():
    if assert_image == True:
        raise(f'The docker image "{image_name}" already exists.')
    return {
        'actions': [(build_image, [], {})],
        'verbosity': 2
    }

def task_push():
    if assert_image == False:
        raise(f'The docker image "{image_name}" does not exist to push.')
    return {
        'actions': [(push_image, [], {})],
        'verbosity': 2
    }

def assert_image(image_name: str) -> bool:
    try:
        client = docker.from_env()
        client.images.get(image_name)
        return True
    except docker.errors.ImageNotFound:
        return False

def build_image() -> bool:
    client = docker.from_env()
    client.images.build(path='.', tag=image_name, rm=True)
    return True

def push_image() -> bool:
    client = docker.from_env()
    image = client.images.get(image_name)
    image.tag(repo, tag=__version__)
    result = client.images.push(f'{repo}:{__version__}')
    if result != None:
        return True
    else:
        return False
