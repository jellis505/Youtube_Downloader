#!/usr/bin/env python
# Created by Joe Ellis and Jessica Ouyang
# Columbia DVMM and NLP Lab Groups
# Logistic Progression -- CUNY NLP/ML/Web Technologies

### Necessary python libraries ###
import os, sys, getopt
import shutil
import subprocess as sub
from gdata.youtube import service
import json
from bs4 import BeautifulSoup
import urllib, urllib2


# Class for interacting with youtube
class YouTubeUtils():
    
    def __init__(self, path_to_youtubedl, download_dir):
        
        #These set up the class variables of where the downloader is 
        self.path_to_youtubedl = path_to_youtubedl

        # Get the path to the Change_Size.py script which is also in the youtube_dl directory
        pos = path_to_youtubedl.rfind("youtube-dl")
        self.path_to_changesize = path_to_youtubedl[:pos] + "ChangeSize.py"

        self.download_dir = download_dir

        # Set up the youtube client, let's see if we can do it without log in
        self.client = service.YouTubeService()

        return

    def DownloadVideo(self,vid_id, resize=False):
        # This downloads the video
        execpath = self.path_to_youtubedl

        # Now create the output directory for this video
        if self.download_dir[-1] == "/":
            download_dir = self.download_dir
        else:
            download_dir = self.download_dir + "/"

        # Create the youtube url using the video id
        url = "http://www.youtube.com/watch?v=" + vid_id

        # This options is what we want to use the 
        o_option = "'%s%s'" % (download_dir,"%(id)s.%(ext)s")

        output = sub.Popen(execpath + " -o " 
                                    + o_option 
                                    + " --write-info-json "
                                    + " --all-subs "
                                    #+ " --write-auto-sub "
                                    + " --write-sub"
                                    + " --sub-lang en "
                                    + url, 
                                    shell=True)
        output.communicate()
        print "Just downloaded the video and info at %s" % url

        # Now we need to resize the video, which is possible using the ChangeSize.py script
        video_file_bak = os.path.join(download_dir,vid_id + "_bak.mp4")
        if resize:
            execpath = self.path_to_changesize
            video_file = os.path.join(download_dir,vid_id + ".mp4")
            video_file_bak = os.path.join(download_dir,vid_id + "_bak.mp4")
            output = sub.Popen(execpath + " -i " + video_file
                                        + " -o " + video_file_bak,
                                        shell=True)
        output.communicate()
        #print "Just Resized the video"

        # Now move the video back to the original file
        if os.path.exists(video_file_bak):
            shutil.copy2(video_file_bak,video_file)
            os.remove(video_file_bak)
        

        #files = os.listdir(download_dir)
        
        #for file_ in files:
        #    if ((".srt" in file_) and (not (".en.srt" in file_) or not (".en-US.srt" in file_))):
        #        os.remove(os.path.join(download_dir,file_))

        #print "Removed all of the other language subtitles besides english that were downloaded"

        return

    def GetCommentsforVideo(self, vid_id):
        # This function gets the comments for a given youtube video
        # The vid_id is the number pattern that appears in the video webpage
        comment_feed = self.client.GetYouTubeVideoCommentFeed(video_id=vid_id)
        video_comments = []
        iter_val = 0
        while comment_feed is not None and (iter_val < 5):
            iter_val += 1
            for comment in comment_feed.entry:
                video_comments.append(comment)
            next_link = comment_feed.GetNextLink()
            if next_link is None:
                comment_feed = None
            else:
                comment_feed = self.client.GetYouTubeVideoCommentFeed(next_link.href)

        # Now let's extract the meaningful portion of the comments, like their
        # name and their comment
        names_and_comments = []
        for video_comment in video_comments:
            soup = BeautifulSoup(str(video_comment).decode("utf-8"))
            name = soup.find("ns0:name")
            content = soup.find("ns0:content")
            if name != None:
                names_and_comments.append((name.string,content.string))

        # This is the file to output the comments to
        output_file = os.path.join(self.download_dir,vid_id + ".comments")
        with open(output_file, "w") as f:
            for name,comment in names_and_comments:
                f.write(name.encode("ascii", "ignore"))
                f.write(" ::: ")
                if comment:
                    f.write(comment.encode("ascii", "ignore").replace("\n", " "))
                f.write("\n")
        
        return names_and_comments


    # This function is not used
    def GetTranscriptforVideo(self, vid_id):
        # This is modified from the python package available at 
        # https://github.com/lasupermarmota/getyoutubecc/blob/master/getyoutubecc.py
        lang = "en"
        cc_url = "http://gdata.youtube.com/api/timedtext?v=" + vid_id + "&lang=" + lang
        print "queried url is: ", cc_url
        print urllib.urlopen(cc_url).read()
        return

    def GetVidsforUser(self,username,start_index,max_results):
        # This function finds the video for a given user, adn returns their ids and publish times
        # TODO: Add 
        video_user_url = "https://gdata.youtube.com/feeds/api/users/"
        query_url = video_user_url + username + "/uploads" + "?start-index=" + str(start_index) + "&max-results=" + str(max_results)
        print query_url
        returned_videos =  urllib2.urlopen(query_url).read()

        # Now let's parse the returned object with Soup
        soup = BeautifulSoup(returned_videos)
        # All we need for each of these is the video id, and published ids
        ids = soup.find_all("id")
        publisheds = soup.find_all("published")
        
        vid_ids_andtime = []
        for id_string, published in zip(ids[1:],publisheds):

            id_string = id_string.string

            id_ = id_string[id_string.string.rfind("/")+1:]
            print id_
            print published.string

            vid_ids_andtime.append((id_,published.string))

        return vid_ids_andtime

    def SearchforVideos(self, search_terms, order_by_term="viewCount"):
        # This function will search for videos based on a given search query
        # Create the query object for the youtube search
        query = service.YouTubeVideoQuery()
        query.vq = search_terms
        query.orderby = order_by_term
        query.racy = "include"
        query.max_results = 50
        returned_results = self.client.YouTubeQuery(query)

        # Now let's parse through the results and get the transcript ids
        soup = BeautifulSoup(str(returned_results).decode("utf-8"))

        vid_ids = soup.find_all("ns0:id")
        author_ids = soup.find_all("ns0:uri")
        published_times = soup.find_all("ns0:published")

        search_vids = []
        for vid_id,author_id,published_time in zip(vid_ids[1:],author_ids[1:],published_times):

            id_string = vid_id.string
            author_id_string = author_id.string

            id_ = id_string[id_string.string.rfind("/")+1:]
            author_id_ = author_id_string[author_id_string.rfind("/")+1:]

            search_vids.append((id_,author_id_,published_time.string))

        return search_vids
# ENDCLASS YouTubeUtils()

def run(argv):
    # This is the run function for this bad boy
    try:
        opts,args = getopt.getopt(argv,"v:u:s:d:p:hn:")
    except getopt.GetoptError:
        print "Usage Error: Please See help"
        sys.exit(1)

    # Priorities that come first are video_id, user, search
    path_to_youtubedl = None
    download_dir = None
    vid_id = None
    serach_terms = None
    user_id = None
    num_to_download = 10
    resize = False
    for opt, arg in opts:
        if opt in ("-h"):
            print "YoutTubeDLer.py -- help instructions"
            print "v: video_id, this is used to download one video"
            print "u: user_id, this is used to download the videos for a particular user"
            print "s: search_terms, this queries youtube given the serach terms discussed"
            print "d: download_dir, the directory to download videos and content too, <MUST BE PROVIDED>"
            print "p: path_to_youtube-dl_executable: like it sounds, <MUST BE PROVIDED>"
            print "n: The number of videos to download <Defaults to 10>"
            print "r: if this flag is added the videos are resized"
            sys.exit(1)
        elif opt in ("-v"):
            vid_id = arg
        elif opt in ("-u"):
            user_id = arg
        elif opt in ("-s"):
            search_terms = arg
        elif opt in ("-d"):
            download_dir = arg
        elif opt in ("-p"):
            path_to_youtubedl = arg
        elif opt in ("-n"):
            num_to_download = int(arg)
        elif opt in ("-r"):
            resize = True

    # Check to make sure that we have the necessary variables
    if not (path_to_youtubedl and download_dir):
        print "You need to supply the path to youtube-dl <p> and download directory <d>"
        sys.exit(1)

    # Initialize the YouTubeUtils class
    ydl = YouTubeUtils(path_to_youtubedl, download_dir)

    # This downloads the info, video, and transcript if available
    if vid_id:
        print "Downloading Video w/ id: ", vid_id
        ydl.DownloadVideo(vid_id, resize)
        ydl.GetCommentsforVideo(vid_id)
        print "Finished Downloading"

    # This downloads the videos from a user, but for now it stops at 10 for a safeguard
    elif user_id:

        print "Downloading %d videos from user: %s" % (num_to_download,user_id)
        # Get the videos for a specified user_id
        for step in range(1,num_to_download,30):
            print "+++++++++++++++++++++++++++++++"
            print step
            vid_ids_and_times = ydl.GetVidsforUser(user_id,step,min(30,num_to_download))


            for vid_id, pub_time in vid_ids_and_times[0:num_to_download]:
                ydl.DownloadVideo(vid_id, resize)
                ydl.GetCommentsforVideo(vid_id)

        print "Finished Downloading"

    elif search_terms:

        print "Downloading videos based on the search term: ", search_terms
        search_results = ydl.SearchforVideos(search_terms)

        for vid_id, author, pub_time in search_results[0:num_to_download]:
            ydl.DownloadVideo(vid_id, resize)
            ydl.GetCommentsforVideo(vid_id)

        print "Finished Downloading"
    
    return


### The Main run portion of the code ###
if __name__ == "__main__":
    run(sys.argv[1:])

    # These are for debug testing purposes
    #ydl = YouTubeUtils("./YouTube_Downloader/youtube-dl", "YouTubeVideos")
    #ydl.DownloadVideo("lQGDqH6rHII")
    #ydl.GetCommentsforVideo("lQGDqH6rHII")
    #ydl.GetTranscriptforVideo("lQGDqH6rHII")
    #ydl.GetVidsforUser("ColumbiaDVMM")
    #ydl.SearchforVideos("Liverpool F.C.")


