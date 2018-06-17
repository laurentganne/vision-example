#!/usr/bin/env python
#
# See https://cloud.google.com/pubsub/docs/reference/libraries
# See https://cloud.google.com/vision/docs/libraries
# https://google-cloud-python.readthedocs.io/en/latest/vision/index.html
import argparse
import json
import time
import os

from google.cloud import pubsub_v1
from google.cloud import storage
from google.cloud import vision
from google.cloud.vision import types
from enum import Enum
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


vision_client = vision.ImageAnnotatorClient()
storage_client = storage.Client()

# font = ImageFont.truetype('arial.ttf', 16)
font = ImageFont.truetype('/Library/Fonts/Arial.ttf', 16)

class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5

# Names of likelihood from google.cloud.vision.enums
likelihood_name = ('UNKNOWN', 'VERY_UNLIKELY', 'UNLIKELY', 'POSSIBLE',
    'LIKELY', 'VERY_LIKELY')

def draw_boxes(image, bounds, color):

    draw = ImageDraw.Draw(image)

    i = 1
    for bound in bounds:
        draw.polygon([
            bound.vertices[0].x, bound.vertices[0].y,
            bound.vertices[1].x, bound.vertices[1].y,
            bound.vertices[2].x, bound.vertices[2].y,
            bound.vertices[3].x, bound.vertices[3].y], None, color)
        draw.text((bound.vertices[0].x, bound.vertices[0].y - 16),'{}'.format(i),(0,0,0),font)
        i += 1
    return image

def get_text_annotations_bounds(annotations, feature):

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

    return bounds

def add_likelihood(likelihood, expected, value, result) {
    if likelihood_name[likelihood] == expected:
        result.append('{}, '.format(value)
}
def get_likelihoods(face) {
    very_likely = ""
    likely = ""
    add_likelihood(face.joy_likelihood, "VERY_LIKELY", "joy", very_likely)
    add_likelihood(face.joy_likelihood, "LIKELY", "joy", likely)
    add_likelihood(face.sorrow_likelihood, "VERY_LIKELY", "sorrow", very_likely)
    add_likelihood(face.sorrow_likelihood, "LIKELY", "sorrow", likely)
    add_likelihood(face.anger_likelihood, "VERY_LIKELY", "anger", very_likely)
    add_likelihood(face.anger_likelihood, "LIKELY", "anger", likely)
    add_likelihood(face.surprise_likelihood, "VERY_LIKELY", "surprise", very_likely)
    add_likelihood(face.surprise_likelihood, "LIKELY", "surprise", likely)
    add_likelihood(face.under_exposed_likelihood, "VERY_LIKELY", "underexposed", very_likely)
    add_likelihood(face.under_exposed_likelihood, "LIKELY", "underexposed", likely)
    add_likelihood(face.blurred_likelihood, "VERY_LIKELY", "blurred", very_likely)
    add_likelihood(face.blurred_likelihood, "LIKELY", "blurred", likely)
    add_likelihood(face.headwear_likelihood, "VERY_LIKELY", "head wear", very_likely)
    add_likelihood(face.headwear_likelihood, "LIKELY", "head wear", likely)

    result = "-"
    if len(very_likely) > 0:
        result = 'Very likely: {}'.format(very_likely[0:(len(very_likely) - 2)])
        if len(likely) > 0:
            result += '. Likely: {}'.format(likely[0:(len(likely) - 2)])
    elif len(likely) > 0:
        result = 'Likely: {}'.format(likely[0:(len(likely) - 2)])
    
    return result
}

def render_face_annotations(bucket_name, blob_name, faces, html_result):
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    byte_stream = BytesIO()
    blob.download_to_file(byte_stream)
    byte_stream.seek(0)
    image = Image.open(byte_stream)
    draw = ImageDraw.Draw(image)
    
    i = 1
    if len(faces) > 0:
        html_result += """
        <h1>Faces detection</h1>
        <table border="1">
        <tr><th>Face ID</th><th>Likelihood</th></tr>
        """

    for face in faces:
        box = [(vertex.x, vertex.y)
               for vertex in face.bounding_poly.vertices]
        draw.line(box + [box[0]], width=5, fill='#00ff00')
        draw.text((box[0][0], box[0][1] - 16),'{}'.format(i),(0,0,0),font)
        html_result += '<tr><td>{}</td><td>{}</td></tr>'.format(i, get_likelihoods(face))
        i += 1

    if len(faces) > 0:
        html_result += "</table>"

    prefix = os.path.splitext(blob_name)[0]
    image.save('{}_faces.jpg'.format(prefix))
    with open('{}_faces.txt'.format(prefix), 'w') as text_file:
        text_file.write("{}".format(faces))
        

def render_web_annotations(bucket_name, blob_name, annotations):

    prefix = os.path.splitext(blob_name)[0]
    with open('{}_web.txt'.format(prefix), 'w') as text_file:
        if annotations.pages_with_matching_images:
            for page in annotations.pages_with_matching_images:
                text_file.write('{}\n'.format(page.url))

def render_label_annotations(bucket_name, blob_name, annotations):

    for label in labels:
        print(label.description)

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
    draw_boxes(image, bounds, 'green')

    prefix = os.path.splitext(blob_name)[0]
    image.save('{}_full_text.jpg'.format(prefix))
    with open('{}_full_text.txt'.format(prefix), 'w') as text_file:
        text_file.write("{}".format(annotations))



def annotate(bucket_name, blob_name):
    imageURI = 'gs://{}/{}'.format(bucket_name, blob_name)
    print('Annotating {}'.format(imageURI))
    response = vision_client.annotate_image({
        'image': {'source': {'image_uri': imageURI}},
        'features': [
            {'type': vision.enums.Feature.Type.FACE_DETECTION},
            {'type': vision.enums.Feature.Type.DOCUMENT_TEXT_DETECTION},
            {'type': vision.enums.Feature.Type.LABEL_DETECTION},
            {'type': vision.enums.Feature.Type.WEB_DETECTION}
        ]})
    #json.dump(response, open('{}.json'.format(image), 'w'))
    #print('Created file {}.json'.format(image))
    # Manage response.web_detection as well as
    # full_text_annotation label_annotations logo_annotations
    # and face_annotations
    # print('Response annotations:\n{}'.format(response.face_annotations))
    html_result = """
    <html>
    <head></head>
    <title>Vision results</tile>
    <body><p>Hello World!</p></body>
    </html>
    """
    render_face_annotations(bucket_name, blob_name, response.face_annotations, html_result)
    render_full_text_annotation(bucket_name, blob_name, response.full_text_annotation)
    render_web_annotations(bucket_name, blob_name, response.web_detection)
    render_label_annotations(bucket_name, blob_name, response.label_annotations)
    html_result += """
    </body>
    </html>
    """
   prefix = os.path.splitext(blob_name)[0]
    with open('{}_detection_result.html'.format(prefix), 'w') as text_file:
        text_file.write("{}".format(html_result))

   prefix = os.path.splitext(blob_name)[0]
    with open('{}_full_text.txt'.format(prefix), 'w') as text_file:
        text_file.write("{}".format(annotations))

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
# annotate('yorc-demo-vision-input', 'atos-bull-sequana.jpg')
annotate('yorc-demo-vision-input', 'atos-cea.jpg')
