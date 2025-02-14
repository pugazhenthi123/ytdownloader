import os
import yt_dlp as ydl
from flask import Flask, render_template, request, send_from_directory, flash, redirect
import tkinter as tk
from tkinter import filedialog

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

DEFAULT_DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(DEFAULT_DOWNLOAD_DIR):
    os.makedirs(DEFAULT_DOWNLOAD_DIR)


# Route to fetch available video formats
@app.route('/')
def index():
    return render_template('index.html')


# Route to fetch formats and display them
@app.route('/fetch_formats', methods=['POST'])
def fetch_formats():
    url = request.form.get('url')
    if not url:
        flash("Please enter a valid URL", "danger")
        return redirect('/')

    formats = get_video_formats(url)
    if not formats:
        flash("No formats available for this video", "danger")
        return redirect('/')

    return render_template('formats.html', formats=formats, url=url)


# Function to get available formats for the video
def get_video_formats(url):
    ydl_opts = {
        'noplaylist': True,
        'quiet': True,
    }
    try:
        with ydl.YoutubeDL(ydl_opts) as ydl_instance:
            info_dict = ydl_instance.extract_info(url, download=False)
            formats = info_dict.get('formats', [])

            seen_resolutions = set()  # To track resolutions already included
            all_formats = []

            for f in formats:
                resolution = f.get('height', None)
                audio_codec = f.get('acodec', None)
                video_codec = f.get('vcodec', None)
                filesize = f.get('filesize', 'Size not available')

                # Handle 'Size not available' before passing it to the template
                if filesize == 'Size not available':
                    filesize = None  # Or set to an empty string, depending on your template logic

                # Add formats with audio codecs, even if they have the same resolution
                if audio_codec is not None:
                    format_details = {
                        'format_id': f.get('format_id', 'N/A'),
                        'resolution': resolution if resolution else 'N/A',
                        'audio_codec': audio_codec,
                        'video_codec': video_codec if video_codec else 'N/A',
                        'ext': f.get('ext', 'N/A'),
                        'filesize': filesize,
                        'url': f.get('url', None),
                    }
                    all_formats.append(format_details)

                # Include formats without an audio codec only the first time for each resolution
                elif resolution and resolution not in seen_resolutions:
                    seen_resolutions.add(resolution)  # Mark this resolution as seen
                    format_details = {
                        'format_id': f.get('format_id', 'N/A'),
                        'resolution': resolution,
                        'audio_codec': 'None',
                        'video_codec': video_codec if video_codec else 'N/A',
                        'ext': f.get('ext', 'N/A'),
                        'filesize': filesize,
                        'url': f.get('url', None),
                    }
                    all_formats.append(format_details)

            return all_formats
    except Exception as e:
        print(f"Error fetching formats: {str(e)}")
        return []







# Route to handle download
@app.route('/download_video/<format_id>', methods=['GET'])
def download_video(format_id):
    url = request.args.get('url', '')
    if not url or not format_id:
        flash("Please select a valid format", "danger")
        return redirect('/')

    # Ask user to choose download directory
    download_dir = choose_download_location()

    if not download_dir:
        flash("Download location not selected. Aborting download.", "danger")
        return redirect('/')

    # Download video
    ydl_opts = {
        'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
        'format': format_id,
        'quiet': False,
    }

    try:
        with ydl.YoutubeDL(ydl_opts) as ydl_instance:
            ydl_instance.download([url])

        # After downloading, send the file to the user
        video_title = ydl_instance.extract_info(url)['title']
        video_file = os.path.join(download_dir, f"{video_title}.mp4")

        if os.path.exists(video_file):
            return send_from_directory(download_dir, f"{video_title}.mp4", as_attachment=True)
        else:
            flash("An error occurred while downloading the video", "danger")
            return redirect('/')

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect('/')


# Function to open a dialog for selecting the download location
def choose_download_location():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    return filedialog.askdirectory(title="Select Download Location")


if __name__ == '__main__':
    app.run(debug=True)
