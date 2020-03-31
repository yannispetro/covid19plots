from flask import Flask, render_template, request, redirect
import requests
import pandas as pd
from bokeh.plotting import figure, output_file, show
from bokeh.embed import components
from bokeh.palettes import Turbo256 as palette
from bokeh.models import Legend
from bokeh.models import NumeralTickFormatter
from bokeh.models import Range1d
from numpy import round, linspace
import math

colorList = list(palette)
featureNames = {'confirmed':'Cases','deaths':'Deaths','recovered':'Recoveries','sick_people':'Sick people'}
plottypeNames = {'cumulative':'Cumulative','new':'New'}

rj = requests.get('https://pomber.github.io/covid19/timeseries.json').json()
rj['United States'] = rj['US']
rj['South Korea'] = rj['Korea, South']
app = Flask(__name__)

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/', methods=['post'])
def my_form_post():
    # country = request.form['country'].replace(' ','').split(',')
    countries = request.form['country'].split(',')
    plottype = request.form['plottype']
    features = request.form.getlist('features')
    xaxis = request.form['xaxis']
    yaxis = request.form['yaxis']

    if xaxis == 'atnumber':
        alignAt = int(request.form['alignat'])
        alignFeature = request.form['align_feature']
        x_axis_type = 'linear'
    else:
        x_axis_type = 'datetime'

    if len(countries) == 0:
        return 'CountryError: Country field is empty'

    TOOLS = "hover,pan,wheel_zoom,box_zoom,reset,save,box_select"
    p = figure(plot_width=1000, plot_height=650, tools=TOOLS,
               title='COVID-19 Daily ' + plottypeNames[plottype] + ' Data',
               x_axis_type=x_axis_type, y_axis_type=yaxis,
               background_fill_color="#fafafa")

    colorIds = round(linspace(0, len(colorList) - 1, len(countries))).astype(int)
    legitems = []
    maxy, maxx = 0, 0
    for j, country in enumerate(countries):
        country = country.rstrip().lstrip()
        color = colorList[colorIds[j]]
        if country not in rj:
            print('CountryError: ' + country + ' is an invalid country name.')
            
        else:
            data = pd.DataFrame(rj[country])
            data['sick_people'] = data['confirmed'] - data['deaths'] - data['recovered']
            data['confirmed_diff'] = data['confirmed'].diff().fillna(data['confirmed']).astype('int')
            data['deaths_diff'] = data['deaths'].diff().fillna(data['deaths']).astype('int')
            data['recovered_diff'] = data['recovered'].diff().fillna(data['recovered']).astype('int')
            data['sick_people_diff'] = data['sick_people'].diff().fillna(data['sick_people']).astype('int')
            #x = pd.to_datetime(data['date'])
            for i in range(len(features)):
                if xaxis == 'atnumber':
                    data = data[data[alignFeature]>=alignAt]
                    x = list(range(len(data)))
                    p.xaxis.axis_label = 'Days since '+featureNames[alignFeature]+' exceeded '+str(alignAt)
                else:
                    x = pd.to_datetime(data['date'])
                    p.xaxis.axis_label = 'Date'
                y = data[features[i]+'_diff'] if plottype == 'new' else data[features[i]]
                if yaxis == 'log':
                    r1 = p.line(x, y, line_width=2, color=color)
                    if i == 0:
                        r2 = p.circle(x, y, size=5, color=color)
                    elif i == 1:
                        r2 = p.x(x, y, size=5, color=color)
                    else:
                        r2 = p.triangle(x, y, size=5, color=color)
                    legitems.append( (country+' - '+featureNames[features[i]], [r1,r2]) )
                else:
                    r1 = p.vbar(x=x, top=y, width=0.7*8.64e+7, color=color, fill_alpha = 0.3)
                    legitems.append( (country+' - '+featureNames[features[i]], [r1]) )
                # if yaxis == 'log' and xaxis == 'atnumber':
                #     mxy, mxx = max(y), len(x)
                #     maxy = mxy if mxy > maxy else maxy
                #     maxx = mxx if mxx > maxx else maxx
    p.xaxis.axis_label_text_font_size = "25px"
    p.xaxis.major_label_text_font_size = "20px"
    p.yaxis.major_label_text_font_size = "20px"
    p.yaxis[0].formatter = NumeralTickFormatter(format="0")
    # if yaxis == 'log' and xaxis == 'atnumber':
    #     p.x_range=Range1d(-maxx*0.05, maxx*1.05)
    #     p.y_range=Range1d(alignAt-math.log((maxy-alignAt)*0.1), maxy+(maxy-alignAt)*0.1)
    #     p.line([0,10],[alignAt,maxy], color='gray')

    leg = Legend(items=legitems, location='center')
    p.add_layout(leg, 'right')


    script, div = components(p)

    return render_template("graph.html", script=script, div=div)
    # return '_'.join([country]+features)

@app.route('/about')
def about():
  return render_template('about.html')

if __name__ == '__main__':
  app.run(port=33507)
