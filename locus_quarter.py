from __future__ import print_function #Email additional lib due SyntaxError: from __future__ imports must occur at the beginning of the file
import feedparser
import re
from html.parser import HTMLParser
import googlemaps
import json
import io
import sys
import configparser
import ast
import click
import logging

#Libraries required for emailing
import httplib2
import os
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client import client, tools
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import errors, discovery

# Create logger and level
lq_level = 60
logging.addLevelName(lq_level, "LQ")
lq_temp_output_filename = 'lq_temp_output.txt'
lq_logger = logging.getLogger('locus-quarter')

# Create file handler to log output
lq_fh = logging.FileHandler(filename=lq_temp_output_filename, mode="w")
lq_fh.setLevel(lq_level)

# Create stream handler for logging
lq_sh = logging.StreamHandler()
lq_sh.setLevel(logging.DEBUG)

# Create formatter and add to handlers
lq_fh_fmt = logging.Formatter('%(message)s')
lq_fh.setFormatter(lq_fh_fmt)

lq_sh_fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
lq_sh.setFormatter(lq_sh_fmt)

# Add handlers to logger
lq_logger.addHandler(lq_fh)
lq_logger.addHandler(lq_sh)

class locus_quarter:
    def __init__(self, config):
        """
        Generic function to parse the provided confiuration file
        and populate the global variables
        """

        try:
            self.config = config
            parser = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
            parser.read(config)

            #List of variables for Locus Quarter customization
            self.g_list_of_regions_urls = ast.literal_eval(parser.get('LOCUS-QUARTER', 'g_list_of_regions_urls'))
            self.g_list_nearby_types_of_places = ast.literal_eval(parser.get('LOCUS-QUARTER', 'g_list_nearby_types_of_places'))
            self.g_travel_mode = ast.literal_eval(parser.get('LOCUS-QUARTER', 'g_travel_mode'))
            self.g_limit_houses = parser.getint('LOCUS-QUARTER', 'g_limit_houses')
            self.g_limit_search_places_nearby = parser.getint('LOCUS-QUARTER', 'g_limit_search_places_nearby')
            self.g_office_addresses = ast.literal_eval(parser.get('LOCUS-QUARTER', 'g_office_addresses'))
            self.g_office_travel_mode = ast.literal_eval(parser.get('LOCUS-QUARTER', 'g_office_travel_mode'))

            #List of variables for configuring Google Developer Account for API access
            self.g_google_maps_client_api_key = parser.get('GOOGLE-API', 'g_google_maps_client_api_key')
            self.g_google_maps_client_api_client = googlemaps.Client(key=self.g_google_maps_client_api_key)
        except configparser.DuplicateOptionError as ErrDupConfigVal:
            lq_logger.critical('Duplicate value found %s' %ErrDupConfigVal)
            raise
        except AttributeError as AttrError:
            lq_logger.critical('Missing key:value in config file %s' %AttrError)
            raise
        except Exception as err:
            lq_logger.critical("Execution error: %s" %err)
            raise
            
    
    def url_loop(self):
        """
        Base loop to read Funda RSS feeds call methods for calculations
        """
        destination_filter_pattern = r"(Te koop: )(.*)"
        for locations in self.g_list_of_regions_urls:
            feed = feedparser.parse(locations)
            feed_title = feed['feed']['title']
            feed_entries = feed.entries

            if len(feed_entries) > 0:
                for cnt, entry in enumerate(feed_entries, start=0):
                    if cnt < self.g_limit_houses:
                        lq_logger.log(lq_level, '+-------------------------------------------------------------+')
                        lq_logger.log(lq_level, entry.link)
                        destination = re.search(destination_filter_pattern, entry.title)
                        src_lat_lng, src_formatted_address = self.src_geocode(destination.group(2))
                        lq_logger.log(lq_level, src_formatted_address)
                        lq_logger.log(lq_level, "Date published:%s" %entry.published)
                        parser = MyHTMLParser()
                        parser.feed(entry.summary)
                        parser.close()
                        self.places_nearby_src(src_lat_lng)
                        self.distance_to_office(src_lat_lng)
            else:
                lq_logger.log(lq_level,'No houses found in the Funda RSS feeds for the given criteria in the config file')

    def src_geocode(self, house_address):
        """
        Receive the house address, call google places api
        Return the geocode (lat,lng) and complete formatted address
        """
        try:
            src_geocode_result = self.g_google_maps_client_api_client.geocode(house_address)
            src_formatted_address = src_geocode_result[0]['formatted_address']
            src_lat_lng = src_geocode_result[0]['geometry']['location']
            return src_lat_lng, src_formatted_address
        except AttributeError as AttrError:
            lq_logger.critical('Missing key:value in config file %s' %AttrError)
            raise
        except Exception as err:
            lq_logger.critical("Execution error: %s" %err)
            raise


    def places_nearby_src(self, p_src_lat_lng):
        """
        Based on the received geocode (lat,lng) of the place
        find nearby places using google places api
        places can be like, restaurants, schools etc
        this can be configured in the configuration file
        """
        for types in self.g_list_nearby_types_of_places:
            places_nearby = self.g_google_maps_client_api_client.places_nearby(location=p_src_lat_lng, type=types, rank_by='distance')
            for cnt, places in enumerate(places_nearby['results'], start=0):
                if cnt < self.g_limit_search_places_nearby:
                    places_geocode = places['geometry']['location']
                    places_name = places['name']
                    lq_logger.log(lq_level, "Facility Type:%s\nFacility Name:%s" %(types, places_name))
                    self.distnace_of_near_places_from_src(p_src_lat_lng, places_geocode)

    def distnace_of_near_places_from_src(self, p_src_lat_lng, p_places_geocode):
        """
        Receive the geocode (lat,lng) of the place and nearby place
        calculate distance based on different means, like walking, cycling etc
        this can be configured in the configuration file
        """
        for travel_mode in self.g_travel_mode:
            distance_calc = self.g_google_maps_client_api_client.distance_matrix(origins=p_src_lat_lng, mode=travel_mode, destinations=p_places_geocode)
            try:
                distance = distance_calc['rows'][0]['elements'][0]['distance']['text']
                duration = distance_calc['rows'][0]['elements'][0]['duration']['text']
                lq_logger.log(lq_level, "Travel type:%s Distance:%s Time:%s" %(travel_mode, distance, duration))
            except KeyError:
                pass

    def distance_to_office(self, p_src_lat_lng):
        """
        Calculate distance to specific address which will be commuted to regularly, like Office
        """
        for travel_mode in self.g_office_travel_mode:
            office_distance_calc = self.g_google_maps_client_api_client.distance_matrix(origins=p_src_lat_lng, mode=travel_mode, destinations=self.g_office_addresses)
            try:
                for num_of_destinations in range(0, len(office_distance_calc['destination_addresses'])):
                    distance = office_distance_calc['rows'][0]['elements'][num_of_destinations]['distance']['text']
                    duration = office_distance_calc['rows'][0]['elements'][num_of_destinations]['duration']['text']
                    lq_logger.log(lq_level, "Travel type:%s To:%s Distance:%s Time:%s" %(travel_mode, office_distance_calc['destination_addresses'][num_of_destinations], distance, duration))
            except KeyError:
                pass


class mail():
    """
    try:
        import argparse
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    except ImportError:
        flags = None
    """
    def __init__(self, config):

        try:
            self.config = config
            parser = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
            parser.read(config)

            #List of variables for Email
            self.g_gmail_secrets_path = parser.get('EMAIL', 'g_gmail_secrets_path')
            self.g_gmail_secret_json = parser.get('EMAIL', 'g_gmail_secret_json')
            self.g_gmail_action_scope = parser.get('EMAIL', 'g_gmail_action_scope')
            self.g_gmail_client_secret_file = parser.get('EMAIL', 'g_gmail_client_secret_file')
            self.g_gmail_google_developer_application_name = parser.get('EMAIL', 'g_gmail_google_developer_application_name')
            self.g_receiver_mail_address = parser.get('EMAIL', 'g_receiver_mail_address')
            self.g_sender_mail_address = parser.get('EMAIL', 'g_sender_mail_address')
            self.g_email_subject = parser.get('EMAIL', 'g_email_subject')

        except configparser.DuplicateOptionError as ErrDupConfigVal:
            lq_logger.critical('Duplicate value found %s' %ErrDupConfigVal)
        except AttributeError as AttrError:
            lq_logger.critical('Missing key:value in config file %s' %AttrError)
        except Exception as err:
            lq_logger.critical("Execution error: %s" %err)

    def send_mail(self):
        """
        Get contents from file to be sent as email body
        """
        with open(file=lq_temp_output_filename, mode='r') as fileoutput:
            file_content = fileoutput.read()
        fileoutput.close()
        self.gmail(file_content, file_content)

    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        try:
            home_dir = os.path.expanduser(self.g_gmail_secrets_path)
            credential_dir = os.path.join(home_dir, '')
            if not os.path.exists(credential_dir):
                os.makedirs(credential_dir)
            credential_path = os.path.join(credential_dir,
                                        self.g_gmail_secret_json)
        
        

            store = Storage(credential_path)
            credentials = store.get()
            if not credentials or credentials.invalid:
                flow = client.flow_from_clientsecrets(self.g_gmail_client_secret_file, self.g_gmail_action_scope)
                flow.user_agent = self.g_gmail_google_developer_application_name
                if flags:
                    credentials = tools.run_flow(flow, store, flags)
                else: # Needed only for compatibility with Python 2.6
                    credentials = tools.run(flow, store)
                print('Storing credentials to ' + credential_path)
            return credentials
        except PermissionError as PermErr:
            lq_logger.critical('Permission on path denied error/Path does not exist %s' %PermErr)
            raise
        except Exception as err:
            lq_logger.critical("Execution error: %s" %err)
            raise

    def SendMessageInternal(self, service, user_id, message):
        """
        Send gmail message and return message id
        """
        try:
            message = (service.users().messages().send(userId=user_id, body=message).execute())
            print('Message Id: %s' % message['id'])
            return message
        except errors.HttpError as error:
            print('An error occurred: %s' % error)

    def SendMessage(self, sender, to, subject, msgHtml, msgPlain):
        """
        Create connection and compose mail
        """
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)
        message1 = self.CreateMessage(sender, to, subject, msgHtml, msgPlain)
        self.SendMessageInternal(service, "me", message1)

    def CreateMessage(self, sender, to, subject, msgHtml, msgPlain):
        """
        Compose email
        """
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to
        msg.attach(MIMEText(msgPlain, 'plain'))
        raw = base64.urlsafe_b64encode(msg.as_bytes())
        raw = raw.decode()
        body = {'raw': raw}
        return body

    def gmail(self, houses_html, houses_plain):
        """Shows basic usage of the Gmail API.
        Creates a Gmail API service object and outputs a list of label names
        of the user's Gmail account.
        """
        try:
            credentials = self.get_credentials()
            http = credentials.authorize(httplib2.Http())
            service = discovery.build('gmail', 'v1', http=http)
            to = self.g_receiver_mail_address
            sender = self.g_receiver_mail_address
            subject = self.g_email_subject
            msgHtml = houses_html
            msgPlain = houses_plain
            self.SendMessage(sender, to, subject, msgHtml, msgPlain)
        except AttributeError as AttrErr:
            lq_logger.critical('Missing attributes for email, caused due to incorrect config values %s' %AttrErr)
            raise

class MyHTMLParser(HTMLParser):
    def handle_data(self, data):
        """
        Parse HTML output and extract information
        """
        html_filter_pattern = r"[0-9].*"
        if ("m2" in data or "." in data and "k.k" not in data):
            x = re.search(html_filter_pattern, data)
            try: 
                lq_logger.log(lq_level, x.group(0))
            except AttributeError:
                lq_logger.warning("1 or more attribute data not found")


@click.command()
@click.option('--address', default=None)
@click.option('--config', default='config-locus-quarter.ini')
@click.option('--email', is_flag=False)
def main(address, config, email):
    lq = locus_quarter(config)

    try:
        if not (address):
            lq.url_loop()
        else:
            src_lat_lng, src_formatted_address = lq.src_geocode(address)
            lq_logger.log(lq_level, '+-------------------------------------------------------------+')
            lq_logger.log(lq_level, src_formatted_address)
            lq.places_nearby_src(src_lat_lng)
            lq.distance_to_office(src_lat_lng)
            lq_logger.log(lq_level, '+-------------------------------------------------------------+')

        del lq
    except TypeError as TypeErr:
        lq_logger.critical('Type error in values passed to methods/functions %s' %TypeErr)
        raise
    except Exception as err:
        lq_logger.critical("Execution error: %s" %err)
        raise

    if (email):
        email = mail(config)
        email.send_mail()
        del email

if __name__ == '__main__':
    main()
