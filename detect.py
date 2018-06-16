#!/usr/bin/env python
#
# See https://cloud.google.com/pubsub/docs/reference/libraries
# See https://cloud.google.com/vision/docs/libraries
# https://google-cloud-python.readthedocs.io/en/latest/vision/index.html
import argparse
import json
import time

from google.cloud import pubsub_v1
from google.cloud import storage
from google.cloud import vision
from google.cloud.vision import types
from enum import Enum
from io import BytesIO
from PIL import Image, ImageDraw


vision_client = vision.ImageAnnotatorClient()
storage_client = storage.Client()


class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5


def draw_boxes(image, bounds, color):
    """Draw a border around the image using the hints in the vector list."""
    # [START draw_blocks]
    draw = ImageDraw.Draw(image)

    for bound in bounds:
        draw.polygon([
            bound.vertices[0].x, bound.vertices[0].y,
            bound.vertices[1].x, bound.vertices[1].y,
            bound.vertices[2].x, bound.vertices[2].y,
            bound.vertices[3].x, bound.vertices[3].y], None, color)
    return image
    # [END draw_blocks]

def get_text_annotations_bounds(annotations, feature):
    # [START detect_bounds]
    """Returns document bounds given an image."""

    bounds = []

    # Collect specified feature bounds by enumerating all document features
    for page in annotations.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:
                        if (feature == FeatureType.SYMBOL):
                            bounds.append(symbol.bounding_box)

                    if (feature == FeatureType.WORD):
                        bounds.append(word.bounding_box)

                if (feature == FeatureType.PARA):
                    bounds.append(paragraph.bounding_box)

            if (feature == FeatureType.BLOCK):
                bounds.append(block.bounding_box)

        if (feature == FeatureType.PAGE):
            bounds.append(block.bounding_box)

    # The list `bounds` contains the coordinates of the bounding boxes.
    # [END detect_bounds]
    return bounds

def render_full_text_annotation(bucket_name, blob_name, annotations):
    # [START render_doc_text]
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    byte_stream = BytesIO()
    blob.download_to_file(byte_stream)
    byte_stream.seek(0)
    image = Image.open(byte_stream)

    bounds = get_text_annotations_bounds(annotations, FeatureType.PAGE)
    draw_boxes(image, bounds, 'blue')
    bounds = get_text_annotations_bounds(annotations, FeatureType.PARA)
    draw_boxes(image, bounds, 'red')
    bounds = get_text_annotations_bounds(annotations, FeatureType.WORD)
    draw_boxes(image, bounds, 'yellow')

    image.save("tmp.jpg")
    # [END render_doc_text]


def annotate(bucket_name, blob_name):
    imageURI = 'gs://{}/{}'.format(bucket_name, blob_name)
    print('Annotating {}'.format(imageURI))
    response = vision_client.annotate_image({
        'image': {'source': {'image_uri': imageURI}},
        'features': [
            {'type': vision.enums.Feature.Type.FACE_DETECTION},
            {'type': vision.enums.Feature.Type.LABEL_DETECTION},
            {'type': vision.enums.Feature.Type.LOGO_DETECTION},
            {'type': vision.enums.Feature.Type.DOCUMENT_TEXT_DETECTION},
            {'type': vision.enums.Feature.Type.WEB_DETECTION}
        ]})
    #json.dump(response, open('{}.json'.format(image), 'w'))
    #print('Created file {}.json'.format(image))
    # Manage response.web_detection as well as
    # full_text_annotation label_annotations logo_annotations
    # and face_annotations
    # print('Response annotations:\n{}'.format(response.face_annotations))
    render_full_text_annotation(bucket_name, blob_name, response.full_text_annotation)

def summarize(message):
    # [START parse_message]
    data = message.data.decode('utf-8')
    attributes = message.attributes

    event_type = attributes['eventType']
    bucket_id = attributes['bucketId']
    object_id = attributes['objectId']
    generation = attributes['objectGeneration']
    description = (
        '\tEvent type: {event_type}\n'
        '\tBucket ID: {bucket_id}\n'
        '\tObject ID: {object_id}\n'
        '\tGeneration: {generation}\n').format(
            event_type=event_type,
            bucket_id=bucket_id,
            object_id=object_id,
            generation=generation)

    if 'overwroteGeneration' in attributes:
        description += '\tOverwrote generation: %s\n' % (
            attributes['overwroteGeneration'])
    if 'overwrittenByGeneration' in attributes:
        description += '\tOverwritten by generation: %s\n' % (
            attributes['overwrittenByGeneration'])

    payload_format = attributes['payloadFormat']
    if payload_format == 'JSON_API_V1':
        object_metadata = json.loads(data)
        size = object_metadata['size']
        content_type = object_metadata['contentType']
        metageneration = object_metadata['metageneration']
        description += (
            '\tContent type: {content_type}\n'
            '\tSize: {object_size}\n'
            '\tMetageneration: {metageneration}\n').format(
                content_type=content_type,
                object_size=size,
                metageneration=metageneration)
    return description
    # [END parse_message]

def poll_notifications(project, subscription_name):
    """Polls a Cloud Pub/Sub subscription for new GCS events for display."""
    # [BEGIN poll_notifications]
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        project, subscription_name)

    def callback(message):
        print('Received message:\n{}'.format(summarize(message)))
        message.ack()
        if 'OBJECT_FINALIZE' ==  message.attributes['eventType']:
            annotate( message.attributes['bucketId'], message.attributes['objectId'])

    subscriber.subscribe(subscription_path, callback=callback)

    # The subscriber is non-blocking, so we must keep the main thread from
    # exiting to allow it to process messages in the background.
    print('Listening for messages on {}'.format(subscription_path))
    while True:
        time.sleep(60)
    # [END poll_notifications]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'project',
        help='The ID of the project that owns the subscription')
    parser.add_argument('subscription',
                        help='The ID of the Pub/Sub subscription')
    args = parser.parse_args()
# poll_notifications(args.project, args.subscription)
annotate('yorc-demo-vision-input', 'atos-bull-sequana.jpg')
