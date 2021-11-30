import urllib
import uuid
import os
from urllib.parse import urlparse
import ssl
import shutil
import urllib.request
import hashlib
import pickle
import errno


def generate_submission(submission):
    # print(submission.title)

    images = []
    if 'is_gallery' in dir(submission) and submission.gallery_data is not None:
        for item in submission.gallery_data.popitem()[1]:
            # print(item['media_id'])
            images.append('https://i.redd.it/' + item['media_id'] + '.jpg')
    # print(dir(submission))
    attr = {'title': submission.title, 'author': submission.author.name, 'media': images,
            'subreddit': submission.subreddit.display_name,
            'permalink': 'https://reddit.com' + submission.permalink,
            'is_original_content': submission.is_original_content,
            'selftext': submission.selftext, 'name': submission.name, 'id': submission.id,
            'created': submission.created_utc}
    if submission.media is not None:
            if 'reddit_video' in submission.media:
                attr["video"] = (submission.media['reddit_video']['hls_url'])
            elif 'oembed' in submission.media:
                attr['media_copy'] = submission.media
                # attr['video'] = submission.media['oembed']['thumbnail_url'].replace('.jpg', '.mp4')
    elif 'preview' in dir(submission):
        images.append(submission.url)
        attr['media']=images
    # print(images)

    return attr


def image_downloader(post, file_store = ''):
    files = []
    for image in post['media']:
        if 'http' in image:
            a = urlparse(image)
            extention = os.path.splitext(a.path)[1]
            if extention == '':
                if 'redgifs.com' in image:
                    image = 'https://thumbs2.redgifs.com/'+os.path.basename(a.path)+'.mp4'
                    a = urlparse(image)
                elif 'https://imgur.com' in image:
                    files.append(image)
                    continue
                else:
                    continue
            # print(a.path)
            # print(os.path.splitext(a.path))
            # print(os.path.basename(a.path))
            # print(image)
            if len(extention) == 0:
                midFolder = ''
            else:
                midFolder = extention.replace('.','') + '/'
            local = file_store + midFolder + uuid.uuid4().hex + extention
            url = image
            file_name = local
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            try:
                path_checker(file_name)
                with urllib.request.urlopen(url, context=ctx) as response, open(file_name, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                hash = hash_file(file_name)
                local = file_store + midFolder + hash + extention
                os.rename(file_name, local)
                files.append(local)

            except urllib.error.HTTPError:
                print("http error")
            except urllib.error.URLError:
                print("url error")
            except UnicodeEncodeError:
                print("unicode error")
    return files


def hash_file(uri):
    BUF_SIZE = 65536
    # md5 = hashlib.md5()
    sha1 = hashlib.sha1()

    with open(uri, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            # md5.update(data)
            sha1.update(data)
    return sha1.hexdigest()


def hash_data(data):
    BUF_SIZE = 65536
    sha1 = hashlib.sha1()
    sha1.update(data)
    return sha1.hexdigest()


def get_varible(file, default):
    try:
        with open(file, 'rb') as handle:
            return pickle.load(handle)
    except IOError or FileNotFoundError:
        save_varible(file, default)
        return default


def save_varible(file, content):
    path_checker(file)
    with open(file, 'wb+') as f:
        pickle.dump(content, f, pickle.HIGHEST_PROTOCOL)


def path_checker(filename):
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except FileNotFoundError:
            do = "nothing"
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
