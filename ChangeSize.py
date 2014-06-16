#!/usr/bin/env python
#
# Created by Joe Ellis for the Personalized Televsion News Project
# Change_Size.py
# This file finds out the size of a video and then changes it to a size that is better for processing, (aka taking it down from HD to SD)

import subprocess, re, string, sys
import getopt

def get_size(pathtovideo):
	# This section runs ffmpeg and pipes the output to stdout and stderr
	p = subprocess.Popen(['ffmpeg', '-i', pathtovideo],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE);
	stdout, stderr = p.communicate();
	# make the possible regular expressions that we need
	
	# Create a list of possible patterns
	possible_patterns = [re.compile(r'Stream.*Video.*([0-9]{4,})x([0-9]{4,})'), \
            			re.compile(r'Stream.*Video.*([0-9]{4,})x([0-9]{3,})'), \
				re.compile(r'Stream.*Video.*([0-9]{3,})x([0-9]{3,})')]

	# Loop through the patterns to try to find the size of the video
	for pattern in possible_patterns:
		print stderr;
		match = pattern.search(stderr)
		if match!=None:
        		x, y = map(int, match.groups()[0:2])
        		break

	if match== None:
		print 'Could Not Get Video Dimensions'
		x = y = 0;
	
	# Now let's get the aspect ratios
	possible_patterns = [re.compile(r'Stream.*Video.*SAR ([0-9]{2,}):([0-9]{1,}) DAR ([0-9]{2,}):([0-9]{1,})'), \
				re.compile(r'Stream.*Video.*SAR ([0-9]{1,}):([0-9]{1,}) DAR ([0-9]{2,}):([0-9]{1,})'), \
				re.compile(r'Stream.*Video.*SAR ([0-9]{2,}):([0-9]{1,}) DAR ([0-9]{1,}):([0-9]{1,})'), \
				re.compile(r'Stream.*Video.*SAR ([0-9]{1,}):([0-9]{1,}) DAR ([0-9]{1,}):([0-9]{1,})')];
	
	# Loop through the possible patterns to get the aspect ratio
	for pattern in possible_patterns:
		match = pattern.search(stderr);
		if match != None:
			a,b,c,d = map(int, match.groups()[0:4])
			break;
	
	if match == None:
		print 'Could Not Get Aspect Ratio'
		a = b = c = d = 0;
		
		
	return x,y,a,b,c,d;

def change_size(pathtovideo,pathto_new_video,SAR,DAR,old_x,old_y, start_time, duration):
	
	# Here is where we will change the aspect ratio and resize the video
	perform_transcoding = True;
	dont_use_aspect = False
	if (SAR[0] == SAR[1]) and (old_x != 640):
		if (DAR[0] == 16) and (DAR[1] == 9):
			# Now set up the parameters for the ffmpeg call
			aspect_str = '%d:%d' % (DAR[0],DAR[1]);
			size_str = '%d:%d' % (640,360);
		elif (DAR[0] == 4) and (DAR[1] == 3):
			aspect_str = '%d:%d' % (DAR[0], DAR[1]);
			size_str = '%d:%d' % (640,480);
		elif (SAR == (0,0) and DAR == (0,0)):
			size_str = '%d:%d' % (640,480);
			aspect_str = '%d:%d' % (4,3);
		else:
			print 'This aspect ratio is unrecongized not changing the video'		
			perform_transcoding = False;
			print SAR, DAR
	else:
		print 'This video is already standard definition doing nothing to change it'
		perform_transcoding = False;

	if perform_transcoding == True and start_time == None and duration == None: 
		# Now do the actual command to change the video
		output = subprocess.Popen(['ffmpeg','-y', '-i', pathtovideo, '-aspect', aspect_str,'-s',size_str, '-r','29.97', pathto_new_video])
		output.communicate()
	elif perform_transcoding == True and start_time != None and duration == None: 
		# Now do the actual command to change the video
		output = subprocess.Popen(['ffmpeg','-y', '-i', pathtovideo, '-aspect', aspect_str,'-s',size_str, '-r','29.97', '-ss', start_time, pathto_new_video])
		output.communicate()
	elif perform_transcoding == True and start_time != None and duration != None: 
		# Now do the actual command to change the video
		output = subprocess.Popen(['ffmpeg','-y', '-i', pathtovideo, '-aspect', aspect_str,'-s',size_str, '-r', '29.97', '-ss', start_time, '-t', duration, pathto_new_video])
		output.communicate()
	return


if __name__ == '__main__':

	try:
		opts, args = getopt.getopt(sys.argv[1:],'hi:o:s:d:')
	except getopt.GetoptError:
		print 'USAGE ERROR. PLEASE SEE HELP: python GenereateContent.py --help'
		sys.exit(2)
	
	# Set start_time and duration to 0
	start_time = None;
	duration = None;
	
	# Get the opts
	opts, args = getopt.getopt(sys.argv[1:],'hi:o:s:d:');
	
	# Parse through the operations given
	for opt, arg in opts:
		if opt == '-h':
			print 'Transcode Videos from HD to SD'
			print '-i: input video'
			print '-o: ouput video'
			print '-ss: start time'
			print '-d: duration of clip'
			quit()
		elif opt == '-i':
			videofile = arg;
		elif opt == '-o':
			pathto_new_video = arg;
		elif opt == '-s':
			start_time = arg;
		elif opt == '-d':
			duration = arg;
	
	# Print out the Variables we got from the options
	print 'input video:', videofile
	print 'output video:', pathto_new_video
	print 'start_time:', start_time
	print 'duration:', duration
	
	# Get the size of the video
	x,y,a,b,c,d = get_size(videofile)

	# Debug purposes
	print 'The x_size of the video is: ', x;
	print 'The y_size of the video is: ', y;
	print 'The SAR is:', a, ':', b;
	print 'The DAR is:', c, ':', d;
	
	# Set up the variables that belong together in tuples
	SAR = (a,b);
	DAR = (c,d);
	
	# Now perform the transcoding of the video
	change_size(videofile,pathto_new_video,SAR,DAR,x,y, start_time, duration);
