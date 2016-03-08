#! /usr/bin/env python

from lxml import html
from twython import Twython
from flickrapi import FlickrAPI
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import requests, json, random
from StringIO import StringIO

APP_KEY = "xxxxxx"
APP_SECRET = "xxxxxx"
OAUTH_TOKEN = "xxxxxx"
OAUTH_TOKEN_SECRET = "xxxxxx"

api = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

flickr_api_key = "xxxxxx"
flickr_api_secret = "xxxxxx"

flickr = FlickrAPI(flickr_api_key, flickr_api_secret, format='json')

def get_followers():
    """
    Automatically follows all new followers
    """
    following = api.get_friends_ids(screen_name='xxxxxx')
    followers = api.get_followers_ids(screen_name='xxxxxx')

    not_following_back = []
    
    for f in followers['ids']:
        if f not in following['ids']:
                not_following_back.append(f)

    for follower_id in not_following_back:
        try:
            api.create_friendship(user_id=follower_id)
        except Exception as e:
            print("error: %s" % (str(e)))

def get_photo():
	"""
	Get third photo from Flickr interesting list
	"""
	# hit Flickr endpoint
	f = flickr.interestingness.getList(extras='url_z', per_page='100')
	data = json.loads(f.decode('utf-8'))

	# parse out photo URL from JSON
	url = data['photos']['photo'][random.randrange(100)]['url_z']
	return url

def get_name():
	"""
	Get random name from Wikipedia
	"""
	# get wikipedia API endpoint for random article
	wiki_url = "https://en.wikipedia.org/w/api.php?format=json&action=query&list=random&rnlimit=1&rnnamespace=0"
	response = requests.get(wiki_url)
	data = response.json()

	# get title element from JSON response
	title = data['query']['random'][0]['title']
	return title

def get_title():
	"""
	Get random quote
	"""
	# URL for random quote page
	quote_url = "http://www.quotationspage.com/random.php3"
	
	# get page, build etree
	page = requests.get(quote_url)
	tree = html.fromstring(page.text)

	# find list of quote elements
	quote_list = tree.xpath('//dt[@class="quote"]')
	
	#get last quote, split last 4 words, then join
	quote_string = quote_list[-1].text_content()
	split = quote_string.split()[-4:]
	separator = " "
	return separator.join(split).rstrip('.').upper()

def create_image(name, title):
	"""
	Create album cover with artist name, title and Flickr image
	"""
	# get flickr URL
	image_url = get_photo()

	# write jpg to disk
	r = requests.get(image_url, stream=True)
	if r.status_code == 200:
		with open('temp.jpg', 'wb') as f:
			for chunk in r:
				f.write(chunk)

	# create drawing object
	img = Image.open("temp.jpg")
	draw = ImageDraw.Draw(img)

	# calculate font width to fit title onto image
	fontsize = 1
	font = ImageFont.truetype('DejaVuSans-ExtraLight.ttf', fontsize)
	while font.getsize(title)[0] < img.size[0] * 0.78:
		fontsize += 1
		font = ImageFont.truetype('DejaVuSans-ExtraLight.ttf', fontsize)

	# set name font
	bigfont = 1
   	font_bold = ImageFont.truetype("DejaVuSans-BoldOblique.ttf", bigfont)
   	while font_bold.getsize(name)[0] < img.size[0] * 0.9:
   		bigfont += 1
   		font_bold = ImageFont.truetype("DejaVuSans-BoldOblique.ttf", bigfont)

	#draw outline
	draw.text((img.size[0] * 0.05 -1, img.size[1] * 0.05), name, (0,0,0), font=font_bold)
	draw.text((img.size[0] * 0.05 +1, img.size[1] * 0.05), name, (0,0,0), font=font_bold)
	draw.text((img.size[0] * 0.05, img.size[1] * 0.05 -1), name, (0,0,0), font=font_bold)
	draw.text((img.size[0] * 0.05, img.size[1] * 0.05 +1), name, (0,0,0), font=font_bold)
	draw.text((img.size[0] * 0.15 -1, img.size[1] * 0.85), title, (0,0,0), font=font)
	draw.text((img.size[0] * 0.15 +1, img.size[1] * 0.85), title, (0,0,0), font=font)
	draw.text((img.size[0] * 0.15, img.size[1] * 0.85 -1), title, (0,0,0), font=font)
	draw.text((img.size[0] * 0.15, img.size[1] * 0.85 +1), title, (0,0,0), font=font)

    # draw text to object
	draw.text((img.size[0] * 0.05, img.size[1] * 0.05), name, (255,255,255), font=font_bold)
	draw.text((img.size[0] * 0.15, img.size[1] * 0.85), title, (255,255,255), font=font)
	
	# save altered image
	img.save('temp.jpg')

def post_update():
    """
    Posts status message to Twitter
    """
    # generate text elements
    name = get_name()
    title = get_title()
    status = name + ": " + title

    # generate image
    create_image(name, title)

    # put image into StringIO
    image = Image.open('temp.jpg')
    image_io = StringIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)

    # send tweet
    try:
    		response = api.upload_media(media=image_io)
    		api.update_status(status=status, media_ids=[response['media_id']])
    except Exception as e:
        print("error: %s" % (str(e)))

def start():
    """
    Starts the program.
    """
    post_update()
    get_followers()

start()