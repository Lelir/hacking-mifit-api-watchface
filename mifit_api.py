#!/usr/bin/env python3

import argparse
import requests
import urllib.parse
import json
import base64
import datetime

def fail(message):
	print("Error: {}".format(message))
	quit(1)

def mifit_auth_email(email,password):
	print("Logging in with email {}".format(email))
	auth_url='https://api-user.huami.com/registrations/{}/tokens'.format(urllib.parse.quote(email))
	data={
		'state': 'REDIRECTION',
		'client_id': 'HuaMi',
		'redirect_uri': 'https://s3-us-west-2.amazonws.com/hm-registration/successsignin.html',
		'token': 'access',
		'password': password,
	}
	response=requests.post(auth_url,data=data,allow_redirects=False)
	response.raise_for_status()
	redirect_url=urllib.parse.urlparse(response.headers.get('location'))
	response_args=urllib.parse.parse_qs(redirect_url.query)
	if ('access' not in response_args):
		fail('No access token in response')
	if ('country_code' not in response_args):
		fail('No country_code in response')

	print("Obtained access token")
	access_token=response_args['access'];
	country_code=response_args['country_code'];
	return mifit_login_with_token({
		'grant_type': 'access_token',
		'country_code': country_code,
		'code': access_token,
	})

def mifit_login_with_token(login_data):
	login_url='https://account.huami.com/v2/client/login'
	data={
		'app_name': 'com.xiaomi.hm.health',
		'dn': 'account.huami.com,api-user.huami.com,api-watch.huami.com,api-analytics.huami.com,app-analytics.huami.com,api-mifit.huami.com',
		'device_id': '02:00:00:00:00:00',
		'device_model': 'android_phone',
		'app_version': '4.0.9',
		'allow_registration': 'false',
		'third_name': 'huami',
	}
	data.update(login_data)
	response=requests.post(login_url,data=data,allow_redirects=False)
	result=response.json()
	return result;

def minutes_as_time(minutes):
	return "{:02d}:{:02d}".format((minutes//60)%24,minutes%60)

def dump_sleep_data(day, slp):
	print("Total sleep: ",minutes_as_time(slp['lt']+slp['dp']),
		", deep sleep",minutes_as_time(slp['dp']),
		", light sleep",minutes_as_time(slp['lt']),
		", slept from",datetime.datetime.fromtimestamp(slp['st']),
		"until",datetime.datetime.fromtimestamp(slp['ed']))
	if 'stage' in slp:
		for sleep in slp['stage']:
			if sleep['mode']==4:
				sleep_type='light sleep'
			elif sleep['mode']==5:
				sleep_type='deep sleep'
			else:
				sleep_type="unknown sleep type: {}".format(sleep['mode'])
			print(format(minutes_as_time(sleep['start'])),"-",minutes_as_time(sleep['stop']),
				sleep_type)

def dump_step_data(day, stp):
	print("Total steps: ",stp['ttl'],", used",stp['cal'],"kcals",", walked",stp['dis'],"meters")
	if 'stage' in stp:
		for activity in stp['stage']:
			if activity['mode']==1:
				activity_type='slow walking'
			elif activity['mode']==3:
				activity_type='fast walking'
			elif activity['mode']==4:
				activity_type='running'
			elif activity['mode']==7:
				activity_type='light activity'
			else:
				activity_type="unknown activity type: {}".format(activity['mode'])
			print(format(minutes_as_time(activity['start'])),"-",minutes_as_time(activity['stop']),
				activity['step'],'steps',activity_type)

def get_watchface(auth_info,url):
	print("Retrieveing watchface")
	band_data_url=url
	headers={
		'apptoken': auth_info['token_info']['app_token'],
	}
	data={
		'device_type': 'android_phone',
		'userid': auth_info['token_info']['user_id'],
	}
	response=requests.get(band_data_url,params=data,headers=headers)
	print (response)
	# Check if the request was successful (status code 200)
	if response.status_code == 200:
		# Parse JSON content
		content = response.content.decode('utf-8')
		data = json.loads(content)
		
		# Extract URLs from data
		urls = [data["url"]]
		
		# Find URLs ending with .zip
		zip_urls = [url for url in urls if url.endswith('.zip')]
		
		# Download zip files
		for zip_url in zip_urls:
			# Download the zip file
			zip_response = requests.get(zip_url)

			# Check if the request was successful (status code 200)
			if zip_response.status_code == 200:
				# Extract filename from URL
				filename = zip_url.split('/')[-1]
				# Open a file in binary write mode
				with open(filename, "wb") as file:
					# Write the binary content of the response to the file
					file.write(zip_response.content)
				print(f"Zip file '{filename}' downloaded successfully.")
			else:
				# If the request was not successful, print the status code
				print(f"Failed to download zip file. Status code: {zip_response.status_code}")

	# for daydata in response.json()['data']:
		# day = daydata['date_time']
		# print(day)
		# summary=json.loads(base64.b64decode(daydata['summary']))
		# for k,v in summary.items():
			# if k=='stp':
				# dump_step_data(day,v)
			# elif k=='slp':
				# dump_sleep_data(day,v)
			# else:
				# print(k,"=",v)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--email",required=True,help="email address for login")
	parser.add_argument("--password",required=True,help="password for login")
	parser.add_argument("--url",required=True,help="url of qrcode")
	args=parser.parse_args()
	auth_info=mifit_auth_email(args.email,args.password)
	get_watchface(auth_info,args.url)


if __name__== "__main__":
	main()
