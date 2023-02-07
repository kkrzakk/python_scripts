#As argument use provided api path

from pprint import pprint
import argparse
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

parser = argparse.ArgumentParser()
parser.add_argument('path', help='Paste path')
args=parser.parse_args()
values=args.path.split('/')
credentials = GoogleCredentials.get_application_default()

service = discovery.build('compute', 'v1', credentials=credentials)

request = service.instances().get(project=values[2], zone=values[4], instance=values[6])
response = request.execute()

pprint(response['name'])
