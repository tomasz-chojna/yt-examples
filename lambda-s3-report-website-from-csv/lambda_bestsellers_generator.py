import json
import logging
import boto3
import csv
from collections import Counter
import tempfile


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info(f"Received S3 trigger: {json.dumps(event, indent=4)}")

    record = event["Records"][0]

    bucket_name = record["s3"]["bucket"]["name"]
    object_key = record["s3"]["object"]["key"]

    logger.info(f"Started processing for bucket={bucket_name} and object_key={object_key}")

    s3_client = boto3.client("s3")

    with tempfile.NamedTemporaryFile(suffix=".csv") as temp_csv:
        s3_client.download_fileobj(temp_csv.name, object_key, temp_csv)

        with tempfile.NamedTemporaryFile(suffix=".csv") as output_tmp_csv:
            render_bestsellers_html_page(temp_csv.name, output_tmp_csv.name)


def render_bestsellers_html_page(input_csv_path, output_html_path):
    bestsellers = generate_bestsellers_table(input_csv_path)
    html = generate_html(bestsellers)

    with open(output_html_path, "w+") as output_file:
        output_file.write(html)


def generate_html(bestsellers_table):
    def render_table_row(row_data):
        return f"""
        <tr>
            <th scope="row">{row_data["index"]}</th>
            <td>{row_data["product_name"]}</td>
            <td>{row_data["quantity_sum"]}</td>
        </tr>
        """

    return f"""
<!doctype html>
<html>
<head>
    <title>Bestsellers</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet"
          integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
</head>
<body>
<div class="container">
    <table class="table mt-3">
        <thead>
            <tr>
                <th scope="col">#</th>
                <th scope="col">Name</th>
                <th scope="col">Sold Items</th>
            </tr>
        </thead>
        <tbody>
            {"".join(render_table_row(row) for row in bestsellers_table)}
        </tbody>
    </table>
</div>
</body>
</html>
"""


def generate_bestsellers_table(input_csv_path):
    with open(input_csv_path, encoding="latin1") as input_file:
        rows_generator = csv.DictReader(input_file)

        stock_code_descriptions = {}
        bestsellers_counter = Counter()

        for row in rows_generator:
            stock_code_descriptions[row["StockCode"]] = row["Description"]
            bestsellers_counter[row["StockCode"]] += int(row["Quantity"])

        table = []
        for index, (stock_code, quantity_sum) in enumerate(bestsellers_counter.most_common(10)):
            table.append({
                "index": index + 1,
                "product_name": stock_code_descriptions[stock_code],
                "quantity_sum": quantity_sum
            })

        return table


render_bestsellers_html_page("data.csv", "output.html")