

class HTML(object):

    def __init__(self, filename: str, content: str = ''):
        self.filename = filename
        self.content = content

    def add(self, code: str = None):
        self.content += f"""
    <div class="simple">
        {code}
    </div>
"""

    def add_head(self, title: str = None):
        self.content += f"""
<!DOCTYPE HTML>
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>{title}</title>
    <style>
          table.results tbody tr:hover
          {{
          background: yellow;
          }}
          div.main, div.results, div.route, div.simple, div.footer
          {{
          font-family: Verdana, Arial, Helvetica, sans-serif;
          font-size: xx-small;
          margin-bottom: 2em;
          }}
          div.route
          {{
          margin-bottom: 2em;
          }}
          table.simple, table.route
          {{
          border:solid 1px gray;
          border-collapse:collapse;
          font-size: xx-small;
          }}
          table.results
          {{
          border:solid 1px gray;
          border-collapse:collapse;
          font-size: xx-small;
          }}
          table.noborder
          {{
          border:none;
          font-size: xx-small;
          }}
          td.simple, td.results, td.route
          {{
          border:solid 1px gray;
          vertical-align:top;
          padding:5px;
          }}
          td.bold
          {{
          font-weight: bold;
          }}
          th.simple, th.results, th.route
          {{
          border:solid 1px gray;
          vertical-align:center;
          }}
          td.right, th.right
          {{
          text-align:right;
          }}
    </style>
</head>
<body>
<div id='main' class="main">
"""

    def add_headings(self, headings: list = None):
        code = ''
        for idx, el in enumerate(headings):
            n = 2 if idx < 2 else 3 if idx < 3 else 4
            code += f"""
        <h{n}>{el}</h{n}>
"""
        self.content += f"""
    <div id="headings" class="simple">
        {code}
    </div>
"""

    def add_route_table(self, info: dict, route: dict = None):
        right_align = [2, 3]
        thead = ['id', '', 'Radius', 'Dist.', 'Description']
        rows = []
        for wp in route:
            rows.append([wp['name'], wp['type'], wp['radius'], wp['cumulative_dist'], wp['description']])
        self.content += f"""
        <div class="route">
"""
        self.content += create_table(css_class='route', right_align=right_align, thead=thead, tbody=rows)
        times = []
        if not info['start_iteration']:
            times.append(['Startgate:', info['start_time']])
        else:
            for idx, el in enumerate(info['startgates']):
                times.append(['Startgates:' if idx == 0 else ' ', el])
        if not info['stopped_time']:
            times.append(['Deadline:', info['task_deadline']])
        else:
            times.append(['Stopped:', info['stopped_time']])
        self.content += create_table(css_class='bold noborder', tbody=times)
        self.content += f"""
        </div>
"""

    def add_table(self, title: str = None, css_class: str = None, right_align: list = None, thead: list = None, tbody: list = None):
        self.content += f"""
        <div class="{css_class}">
"""
        if title:
            self.content += f"""
            <h4>{title}</h4>
"""
        self.content += create_table(css_class=css_class, right_align=right_align, thead=thead, tbody=tbody)
        self.content += f"""
        </div>
"""

    def add_footer(self, timestamp: str = None):
        self.content += f"""
</div>
<div id='footer' class='footer'>
  <h4>Created by Airscore on {timestamp}</h4>
</div>
</body>
</html>
"""

    def write(self, filename: str = None):
        with open(filename or self.filename, "w") as file:
            file.write(self.content)

    def get_content(self):
        from io import BytesIO
        mem = BytesIO()
        mem.write(self.content.encode('utf-8'))


def create_table(css_class: str = None, right_align: list = None, thead: list = None, tbody: list = None):
    content = f"""
        <table class="{css_class}">
"""
    if thead is not None:
        content += f"""
            <thead>
            <tr>
"""
        for idx, col in enumerate(thead):
            content += f"""
                <th class="{css_class}">{col}</th>
"""
        content += f"""
            </tr>
            </thead>
"""
    if tbody is not None:
        content += f"""
            <tbody>
"""
        for row in tbody:
            content += f"""
            <tr>
"""
            for i, col in enumerate(row):
                cell_class = f'{css_class} right' if right_align and i in right_align else css_class
                content += f"""
                <td class="{cell_class}">{col}</td>
"""
            content += f"""
            </tr>
"""
        content += f"""
            </tbody>
"""
    content += f"""
        </table>
"""
    return content
