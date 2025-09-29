from flask import Flask, request, render_template_string, jsonify
import requests
import os
import re
import time
import threading

# Flask Application Initialize
app = Flask(__name__)
# Debug mode on for local testing, Render will manage it in production.
app.debug = True 

# A dictionary to store running commenter instances, helpful for logging/management
tasks = {}

class FacebookCommenter:
    """Handles the core logic of scraping and posting comments using mbasic Facebook."""
    def __init__(self):
        self.comment_count = 0
        self.stop_flag = False # Flag to stop the loop if needed

    def comment_on_post(self, cookies, post_id, comment):
        """Attempts to post a single comment using session and form data."""
        with requests.Session() as r:
            # Setting necessary headers for mbasic Facebook to simulate a mobile browser request
            r.headers.update({
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'sec-fetch-site': 'none',
                'accept-language': 'id,en;q=0.9',
                'Host': 'mbasic.facebook.com',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-encoding': 'gzip, deflate',
                'sec-fetch-mode': 'navigate',
                'user-agent': 'Mozilla/5.0 (Linux; Android 13; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.166 Mobile Safari/537.36',
                'connection': 'keep-alive',
            })

            # 1. Get the post page to extract form data (fb_dtsg, jazoest, next_action)
            response = r.get(f'https://mbasic.facebook.com/{post_id}', cookies={"cookie": cookies})
            
            next_action_match = re.search('method="post" action="([^"]+)"', response.text)
            fb_dtsg_match = re.search('name="fb_dtsg" value="([^"]+)"', response.text)
            jazoest_match = re.search('name="jazoest" value="([^"]+)"', response.text)

            if not (next_action_match and fb_dtsg_match and jazoest_match):
                # Return an error message to be logged
                return f"Parameters not found for post {post_id}. Cookie issue/post not found.", 400

            next_action = next_action_match.group(1).replace('amp;', '')
            fb_dtsg = fb_dtsg_match.group(1)
            jazoest = jazoest_match.group(1)

            data = {
                'fb_dtsg': fb_dtsg,
                'jazoest': jazoest,
                'comment_text': comment,
                'comment': 'Submit',
            }

            # 2. Post the comment
            r.headers.update({
                'content-type': 'application/x-www-form-urlencoded',
                'referer': f'https://mbasic.facebook.com/{post_id}',
                'origin': 'https://mbasic.facebook.com',
            })

            response2 = r.post(f'https://mbasic.facebook.com{next_action}', data=data, cookies={"cookie": cookies})

            if 'comment_success' in response2.url and response2.status_code == 200:
                self.comment_count += 1
                return f"Comment {self.comment_count} successfully posted. Using cookie: {cookies[:25]}...", 200 # Shorten cookie for log
            else:
                return f"Comment failed with status code: {response2.status_code}. Possible block/limit.", 400


    def process_inputs(self, cookies, post_id, comments, delay):
        """The main loop that runs in a background thread."""
        self.stop_flag = False
        cookie_index = 0

        while not self.stop_flag:
            for comment in comments:
                if self.stop_flag:
                    break

                comment = comment.strip()
                if comment:
                    
                    # Call the commenter function
                    status_message, status_code = self.comment_on_post(cookies[cookie_index], post_id, comment)
                    
                    # Print status to Render logs (Crucial for remote monitoring)
                    print(f"[STATUS] {time.strftime('%Y-%m-%d %H:%M:%S')} - {status_message}") 
                    
                    # Rotate cookie for next attempt
                    cookie_index = (cookie_index + 1) % len(cookies)
                    
                    # Sleep for the specified delay
                    time.sleep(delay)
            
            if self.stop_flag:
                print("[INFO] Commenting process stopped by system.")
                break
        
        print("[INFO] Commenting loop finished.")

@app.route("/", methods=["GET", "POST"])
def index():
    """Handles the web form interface."""
    
    # Simple form HTML template
    form_html = '''
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comment3r</title>
    <style>
        body {
            background-image: url('https://i.ibb.co/wpTPg1Z/5b48a414c78473a908090f05ee6b5d7c.jpg');
            background-size: cover;
            font-family: Arial, sans-serif;
            color: yellow;
            text-align: center;
            padding: 0;
            margin: 0;
            min-height: 100vh;
        }
        .container {
            margin-top: 50px;
            background-color: rgba(0, 0, 0, 0.7); 
            padding: 30px;
            border-radius: 10px;
            display: inline-block;
            box-shadow: 0 0 20px rgba(255, 255, 0, 0.5);
        }
        h1 {
            font-size: 3em;
            color: gold;
            margin-top: 0;
        }
        .status {
            color: cyan;
            font-size: 1.2em;
            margin-bottom: 20px;
        }
        input[type="text"], input[type="number"], input[type="file"] {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border: 1px solid #ccc;
            box-sizing: border-box;
            background-color: #333;
            color: white;
        }
        button {
            background-color: yellow;
            color: black;
            padding: 10px 20px;
            margin-top: 15px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: orange;
        }
        .footer {
            margin-top: 30px;
            color: white;
            font-size: 0.9em;
        }
        a {
            color: cyan;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>OFFLINE POST LOADER</h1>
     <div class="status">꧁ᴏᴡɴᴇʀ ➤ xᴍᴀʀᴛʏ ᴀʏᴜsʜ ᴋɪɴɢ꧂</div>
    <form method="POST" enctype="multipart/form-data">
        Post Uid: <input type="text" name="post_id" required><br>
        Delay (in seconds): <input type="number" name="delay" value="10" required><br>
        Cookies File: <input type="file" name="cookies_file" required><br>
        Comments File: <input type="file" name="comments_file" required><br>
        <button type="submit">Start Sending Comments</button>
        </form>
        
        <div class="footer">
            <a href="https://www.facebook.com/XMARTY.AYUSH.KING.YOUTUBER.420" target="_blank">Contact me on Facebook</a>
        </div>
    </div>
</body>
</html>
    '''

    if request.method == "POST":
        post_id = request.form.get('post_id')
        try:
            delay = int(request.form.get('delay', 10))
        except ValueError:
            return "Invalid delay value. Must be a number.", 400

        cookies_file = request.files.get('cookies_file')
        comments_file = request.files.get('comments_file')

        if not (cookies_file and comments_file):
            return "Cookies and comments files are required.", 400

        # Read files and clean up lines
        cookies = [line.strip() for line in cookies_file.read().decode('utf-8').splitlines() if line.strip()]
        comments = [line.strip() for line in comments_file.read().decode('utf-8').splitlines() if line.strip()]

        if len(cookies) == 0:
            return "Cookies file is empty.", 400
        if len(comments) == 0:
            return "Comments file is empty.", 400
            
        # Initialize Commenter and start the process in a new thread
        commenter = FacebookCommenter()
        
        # We start the loop in a separate thread so the web page can load immediately
        # and the server doesn't time out.
        thread = threading.Thread(
            target=commenter.process_inputs, 
            args=(cookies, post_id, comments, delay)
        )
        thread.daemon = True # Allows the thread to stop when the main process exits
        thread.start()
        
        # Store the running task (optional)
        tasks['current_task'] = commenter 

        # The response tells the user to check the Render Logs for output.
        return """
        <div style="text-align: center; color: yellow; margin-top: 50px; background-color: rgba(0, 0, 0, 0.7); padding: 20px; border-radius: 10px;">
            <h1>Task Started!</h1>
            <p style="color: cyan; font-size: 1.2em;">
                Comments are being posted in the background. **Please check the Render Logs** for real-time updates.
            </p>
            <p style="color: white; font-size: 1em;">
                Go back to the previous page to submit a new task.
            </p>
        </div>
        """

    
    return render_template_string(form_html)

if __name__ == '__main__':
    # Render automatically sets the PORT environment variable. We use 5000 as a fallback for local testing.
    port = int(os.environ.get('PORT', 5000)) 
    app.run(host='0.0.0.0', port=port)

