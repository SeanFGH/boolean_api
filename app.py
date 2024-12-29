from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import base64
import io
import traceback

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "\u5e03\u6797\u4ee3\u6578\u8f49\u63db API \u4e0a\u7dda\u4e2d\uff01"

@app.route('/get_boolean_image', methods=['POST'])
def get_boolean_image():
    """
    \u63a5\u6536 JSON \u683c\u5f0f：
    {
        "expression": "\u9019\u88e1\u653e\u5e03\u6797\u4ee3\u6578\u5f0f"
    }
    \u56de\u50b3\uff1aPNG \u5716\u7247 (image/png)
    """
    try:
        data = request.get_json()
        if not data or 'expression' not in data:
            return jsonify({"error": "\u8acb\u5728 JSON \u4e2d\u63d0\u4f9b 'expression' \u6b04\u4f4d"}), 400

        expression = data['expression']

        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--headless")  # \u555f\u7528\u7121\u982d\u6a21\u5f0f

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        try:
            driver.get("https://www.boolean-algebra.com/")

            wait = WebDriverWait(driver, 20)
            mathquill_div = wait.until(EC.presence_of_element_located((By.ID, "question")))

            driver.execute_script("""
                var mathField = MQ.MathField(arguments[0]);
                mathField.latex(arguments[1]);
            """, mathquill_div, expression)

            submit_btn = wait.until(EC.element_to_be_clickable((By.ID, "submit-btn")))
            driver.execute_script("arguments[0].click();", submit_btn)

            time.sleep(5)

            view_non_minimalized_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'View Non-minimalized')]"))
            )
            driver.execute_script("arguments[0].click();", view_non_minimalized_btn)

            time.sleep(3)

            original_canvas = driver.find_element(By.XPATH, "//div[@id='originalView']/canvas")
            driver.execute_script("arguments[0].scrollIntoView();", original_canvas)
            time.sleep(3)

            try:
                canvas_data_url = driver.execute_script(
                    "return arguments[0].toDataURL('image/png');", 
                    original_canvas
                )
                image_bytes = base64.b64decode(canvas_data_url.split(",")[1])

            except Exception as e:
                original_canvas.screenshot_as_png
                return jsonify({"error": "\u7121\u6cd5\u64f7\u53d6\u5716\u7247"}), 500

        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": f"Selenium \u6d41\u7a0b\u767c\u751f\u932f\u8aa4: {str(e)}"}), 500
        finally:
            driver.quit()

        if image_bytes:
            image_io = io.BytesIO(image_bytes)
            image_io.seek(0)
            return send_file(image_io, mimetype='image/png')
        else:
            return jsonify({"error": "\u672a\u80fd\u6210\u529f\u53d6\u5f97\u5716\u7247\u8cc7\u6599"}), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"\u4f7f\u7528\u6a5f\u767c\u751f\u932f\u8aa4: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
