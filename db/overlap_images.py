from PIL import Image
import requests
from io import BytesIO
import sqlite3


def overlay_images(url, blob_data):
    try:
        # Download the image from the URL
        response = requests.get(url)
        url_image = Image.open(BytesIO(response.content))

        # url_image.show()

        # Open the BLOB image
        blob_image = Image.open(BytesIO(blob_data))

        blob_image.show()

        # Resize the downloaded image to match the size of the BLOB image
        url_image = url_image.resize(blob_image.size)

        # Create a new image with the size of the BLOB image
        result_image = Image.new("RGBA", blob_image.size)

        # Paste the BLOB image onto the new image
        result_image.paste(blob_image, (0, 0))

        # Paste the downloaded image onto the new image with some transparency
        result_image = Image.alpha_composite(result_image, url_image)

        result_image.show()

        return result_image

    except Exception as e:
        print(f"Error: {e}")
        return None


def get_file_data(file_id):
    try:
        with sqlite3.connect('athena.db') as conn:  # Replace 'your_database.db' with your actual database file name
            cur = conn.cursor()
            cur.execute('SELECT template_data FROM concept_templates WHERE id = ?', (file_id,))
            row = cur.fetchone()

            if row:
                file_data = row[0]
                return file_data
            else:
                print(f"File with ID {file_id} not found.")
                return None

    except Exception as e:
        print(f"Error: {str(e)}")
        return None

# Example usage:
file_id = 1  # Replace with the actual file ID you want to retrieve
data = get_file_data(file_id)
url = "https://cdn.discordapp.com/attachments/1169264050396483615/1175687295970594886/pyramiddevelopers_string_7069748253R2D2_and_C3PO_in_a_land_set__fd13b641-c731-4629-820c-86e30cfb5985.png?ex=656c231e&is=6559ae1e&hm=5d0650382a6eca56ce3ed21e2bc9aa84de9ba7cd9859241461a5657a5e6f8338&"

overlay_images(url, data)
