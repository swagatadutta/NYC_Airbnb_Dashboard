from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import dash
import pandas as pd
import numpy as np
import folium
from folium.plugins import FastMarkerCluster
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# format number 
def format_number(number):
    if number < 1000:
        return str(round(number))
    elif number < 1000000:
        return f"{number / 1000:.1f}K"
    else:
        return f"{number / 1000000:.1f}M"

# Load your data
listings_df = pd.read_csv('listings.csv')

# create binned columns
listings_df['minimum_nights_bin']=pd.cut(listings_df['minimum_nights'], 
                                        bins=[-np.inf,5,10,15,20,25,30,60, 90, 120, 150, 180, 210, 240, 270, 300, 330, np.inf],
                                        labels=['<=5', '5-10', '10-15', '15-20', '20-25', '25-30', 
                                                '30-60', '60-90', '90-120', '120-150', '150-180', 
                                                '180-210', '210-240', '240-270', '270-300', '300-330', '>330'])

listings_df['price_bin']=pd.cut(listings_df['price'], 
                                        bins=(-np.inf, 100, 150, 200, 250, 300, 350, 400, 500, 600, 700, 800, 900, 1000,  np.inf), 
                                        labels=['<100', '100-150', '150-200', '200-250', '250-300', '300-350', 
                                                '350-400', '400-500', '500-600', '600-700', '700-800', '800-900', '900-1000', '>1000'])

listings_df['last_1yr_availability']=pd.cut(365-listings_df['availability_365'], 
                                        bins=[-np.inf, 0, 31, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, np.inf], 
                                        labels=['0','1-30', '30-60', '60-90', '90-120', '120-150', '150-180', '180-210', 
                                                '210-240', '240-270', '270-300', '300-330', '>330'])

listings_df['term_rentals']=listings_df['minimum_nights'].apply(lambda x: "Short Term" if x<=30 else "Long Term" if x>30 else x)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Assuming neighbourhoods_df has a 'group' column that we'll use for the neighbourhood-group dropdown
neighbourhood_dropdown_options = [nb for nb in np.sort(listings_df['neighbourhood_group'].unique())]+\
                                 [nb for nb in np.sort((listings_df['neighbourhood_group']+' | '+listings_df['neighbourhood']).unique())]

app.layout = html.Div([
    dbc.Container(fluid=True, children=[
        dbc.Row([
        dbc.Row([
            dbc.Col(html.H1("New York City Airbnb Dashboard", className="mb-2"), width="auto"),
            dbc.Col(dbc.Button("About Dashboard", id="open-info-1", color="primary", className="mb-2 ml-2"),width="auto"),
            dbc.Col(dbc.Button("How to Use this Dashboard", id="open-info-2", color="primary", className="mb-2 ml-2"),width="auto")
        ], align="center"),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("About This Dashboard")),
                dbc.ModalBody(
                    html.Small([html.P("This dashboard is a comprehensive analytical tool designed for current and potential Airbnb hosts, \
                           travel planners, and real estate investors interested in the New York City short-term rental market. \
                           This interactive platform aggregates data to present insightful metrics on listing counts, \
                           types of accommodations, price patterns, occupancy rates, and host operations within the five boroughs of NYC. \
                           It enables users to make informed decisions by offering neighborhood-level granularity and historical trends, \
                           thereby reflecting the dynamics of the local Airbnb market."),
                    html.P("For hosts, it's a valuable resource to benchmark their \
                           properties, for travel planners to understand accommodation availability and pricing, \
                           and for investors to spot market opportunities and assess potential returns."),
                    html.P("The dashboard is intuitive and user-friendly, providing a strategic edge in the competitive NYC accommodation space.")])
                ),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-info-1", className="ml-auto")
                ),
            ],
            id="modal-info-1",
            is_open=False,  # True to show the modal; False to hide it
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Dashboard Usage")),
                dbc.ModalBody(
                    html.Small([html.P("This dashboard allows you to explore Airbnb listings data for New York City. \
                                       You can filter data based on neighborhood, listing type, price range, and more."),
                    html.P("Here are some tips to get you started:"),
                    html.Ul([
                        html.Li("Select different neighborhoods to see localized data."),
                        html.Li("Use the dropdown menus to refine your search."),
                        html.Li("You can select multiple values for Filters 'listing type', 'price bucket'"),
                        html.Li("Hover over the charts to see additional details."),
                        html.Li("Use chart-zoom feature to zoom over bar-charts. Press home button or double click on the chart to go back to default view")
                        ]),
                    html.P("Charts and maps reflect the filtered data interactively."),
                    html.P("Every chart has [ACTION], [INFO] or [INSIGHTS] section where ever applicable."),
                    html.P("The map section of the chart can be used to view listing localities. The listings on map changes with all the filters."),
                    ])),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-info-2", className="ml-auto")
                ),
            ],
            id="modal-info-2",
            is_open=False,  # True to show the modal; False to hide it
        ),
        dbc.Row([dbc.Col(html.Small("Select Area"), className="mb-2"),
                 dbc.Col(html.Small("Check only Superhost listings"), className="mb-2"),
                 dbc.Col(html.Small("listing type"), className="mb-2"),
                 dbc.Col(html.Small("Price bucket"), className="mb-2"),
                 dbc.Col(html.Small("Term of rental"), className="mb-2"),
                 dbc.Col(html.Small("Check only reviewed listings"), className="mb-2"),
                 ]),
        dbc.Row([dbc.Col(dcc.Dropdown(
            id='neighbourhood-dropdown',
            options=[{'label': nb, 'value': nb} for nb in neighbourhood_dropdown_options],
            value=None,  # default value
            multi=False,
            className="mb-2")),

            dbc.Col(dcc.Dropdown(
            id='check-superhost-only',
            options=['Yes', 'No'],
            value='No',  # default value
            multi=False,
            className="mb-2")),

            dbc.Col(dcc.Dropdown(
            id='select-listing-type',
            options=list(listings_df['room_type'].unique()),
            value=None,  # default value
            multi=True,
            className="mb-2")), 
            
            dbc.Col(dcc.Dropdown(
            id='select-price',
            options=['<100', '100-150', '150-200', '200-250', '250-300', '300-350', '350-400', '400-500', '500-600', 
                     '600-700', '700-800', '800-900', '900-1000', '>1000'],
            value=None,  # default value
            multi=True,
            className="mb-2")),
            
            dbc.Col(dcc.Dropdown(
            id='select-term',
            options=['Short Term', 'Long Term'],
            value=None,  # default value
            multi=False,
            className="mb-2")), 
            
            dbc.Col(dcc.Dropdown(
            id='select-reviewed-listings',
            options=['Yes','No'],
            value='No',  # default value
            multi=False,
            className="mb-2"))]   
        ), 
        ], style={'position': 'sticky', 'top': '0px', 'zIndex': '1020','backgroundColor': '#FFFFFF', 'opacity':'1' }),
        dbc.Row([
            dbc.Col([
                dbc.Card([dbc.CardBody([html.Div(id='stats-output', className="mb-2")])], className="mb-4"),
                dbc.Card([dbc.CardBody([
                dcc.Graph(id='room-type-distribution', className="mb-2"),
                html.Div(id='room-type-description', className="mb-2"),
                ])], className="mb-4"),
                
                dbc.Card([dbc.CardBody([
                dcc.Graph(id='term_rentals', className="mb-2"),
                html.Div(id='term-rentals-description', className="mb-2"),
                ])], className="mb-4"),

                dbc.Card([dbc.CardBody([
                dcc.Graph(id='last_12m_availability', className="mb-2"),
                dbc.Row([dbc.Row(html.Small(html.Mark("Toggle View")), className="mb-2"),
                         dcc.Dropdown(id='select-average-or-total', 
                                      options=['Show Average Earnings', 'Show Total Earnings'],
                                      value='Show Average Earnings', 
                                      multi=False,
                                      className="mb-2")], style={'width':'50%'}),
                html.Div(id='12m-availability-description', className="mb-2"),
                ])], className="mb-4"),

                dbc.Card([dbc.CardBody([
                dcc.Graph(id='price_distribution', className="mb-2"),
                html.Div(id='price-distribution-description', className="mb-2"),
                ])], className="mb-4"),

                dbc.Card([dbc.CardBody([
                dcc.Graph(id='top_np_price', className="mb-2"),
                html.Div(id='top-nb-price-description', className="mb-2"),
                ])], className="mb-4")
                # ... potentially other components ...
            ], width=5, style={'maxHeight': 'calc(100vh - 50px)', 'overflowY': 'scroll', 'paddingRight': 5}),
            dbc.Col( [
                     html.Div(id='sankey-clickable-wrapper', children=[html.Small(html.Mark("Click to view chart info"))], style={'text-align': 'left', 'width':'20%'}),
                     dcc.Graph(id='sankey-graph', style={'height':'35%', 'padding':'0'}), #dbc.Row(sankey_graph, style={'height':'35%'})
                     dbc.Modal([dbc.ModalBody(
                                              [dcc.Graph(id='sankey-chart-modal'),
                                               html.Small([html.P("   "),
                                                            html.P("[INFO] The Sankey chart presents a progression of Airbnb listings \
                                                                  from New York City boroughs through to their status as Superhost listings. \
                                                                  It traces the listings' journey from borough origin, through accommodation \
                                                                  type and stay duration, to pricing categories, and ultimately their classification as \
                                                                  Superhost, non-Superhost, or unknown Superhost status.\
                                                                  The visual flow between categories allows for insights into the factors \
                                                                  that may influence a listing's likelihood of becoming a Superhost, \
                                                                  such as location, listing type, stay term, and price range."),
                                                            html.P("[INFO] Flow indicates that some NYC boroughs \
                                                                   are more likely to produce Superhost listings, \
                                                                   hinting at factors like local appeal or hosting quality. \
                                                                   It also shows how accommodation type and stay duration may \
                                                                   influence Superhost attainment, and suggests that pricing could play \
                                                                   a role in a listing's Superhost status. Additionally, the chart reveals \
                                                                   data gaps in pricing and Superhost designation, underscoring areas \
                                                                   for potential further research." )
                                                           ])
                                               ,
                                               ]
                                             ),
                                dbc.ModalFooter(dbc.Button("Close", id="close-sankey-modal", className="ml-auto"))
                                ],id="modal-sankey",is_open=False,size="lg",),
                     dbc.Row(html.Iframe(id='map', srcDoc=None, width='100%'),style={ "height":'47%'}),
                    ], 
                    width=7, style={'height': '100vh','position':'fixed', 'top': '130px', 'right': 0, })
        ], className='g-0'),  # Remove gutters between columns
    ], style={'maxWidth': '100%'})
], style={'height': '100vh', 'overflowY': 'auto'})  # Set the overall layout height and hide overflow

# Callback to open the modal
@app.callback(
    Output("modal-sankey", "is_open"),
    [Input("sankey-clickable-wrapper", "n_clicks"), Input("close-sankey-modal", "n_clicks")],
    [State("modal-sankey", "is_open")],
)
def toggle_sankey_modal(sankey_clicks, close_clicks, is_open):
    if sankey_clicks or close_clicks:
        return not is_open
    return is_open


@app.callback(
    Output("modal-info-1", "is_open"),
    [Input("open-info-1", "n_clicks"), Input("close-info-1", "n_clicks")],
    [State("modal-info-1", "is_open")],
)
def toggle_modal_1(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("modal-info-2", "is_open"),
    [Input("open-info-2", "n_clicks"), Input("close-info-2", "n_clicks")],
    [State("modal-info-2", "is_open")],
)
def toggle_modal_1(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    [Output('map', 'srcDoc'), 
     Output('room-type-distribution', 'figure'), 
     Output('stats-output', 'children'), 
     Output('term_rentals', 'figure'), 
     Output('last_12m_availability', 'figure'), 
     Output('price_distribution', 'figure'),
     Output('top_np_price', 'figure'),
     
     Output('room-type-description', 'children'),
     Output('term-rentals-description', 'children'),
     Output('12m-availability-description', 'children'),
     Output('price-distribution-description', 'children'),
     Output('top-nb-price-description', 'children'),

     Output('sankey-graph', 'figure'),
     Output('sankey-chart-modal', 'figure')
     ],

    [Input('neighbourhood-dropdown', 'value'), 
     Input('check-superhost-only', 'value'),
     Input('select-listing-type', 'value'),
     Input('select-price', 'value'),
     Input('select-term', 'value'),
     Input('select-reviewed-listings', 'value'),
     Input('select-average-or-total', 'value')
     ]
)
def update_charts(selected_neighbourhood, check_super_host, listing_type, price_type, term_type,reviewed_listings, view_avg_total):
    if selected_neighbourhood:
        nb_ls = selected_neighbourhood.split(' | ')
        if len(nb_ls)>1:
            filtered_df = listings_df[(listings_df['neighbourhood_group']==nb_ls[0]) & (listings_df['neighbourhood']==nb_ls[1])]
        else:
            filtered_df = listings_df[(listings_df['neighbourhood_group']==nb_ls[0])]
    else:
        filtered_df=listings_df.copy()

    if check_super_host=='Yes':
        filtered_df=filtered_df[filtered_df['host_is_superhost']=='t']
    else:
        None
    
    if listing_type:
        filtered_df=filtered_df[filtered_df['room_type'].isin(listing_type)]
    else:
        None

    if price_type:
        filtered_df=filtered_df[filtered_df['price_bin'].isin(price_type)]
    else:
        None

    if term_type=='Short Term':
        filtered_df=filtered_df[filtered_df['term_rentals']=="Short Term"]
    elif term_type=='Long Term':
        filtered_df=filtered_df[filtered_df['term_rentals']=="Long Term"]
    else:
        term_type=''
    
    if reviewed_listings=='Yes':
        filtered_df=filtered_df[filtered_df['number_of_reviews']>1]
    else:
        None

    # Create Folium map
    if filtered_df['neighbourhood_group'].nunique()>1:
        zoom=10
    else:
        if filtered_df['neighbourhood'].nunique()>1:
            zoom=11
        else:
            zoom=14


    # Create Sankey chart preprocess data
    sankey_df=filtered_df[['id', 'neighbourhood_group', 'room_type', 'minimum_nights', 'price', 'host_is_superhost']]
    sankey_df['minimum_nights']=sankey_df['minimum_nights'].apply(lambda x: 'Long Term' if x>30 else 'Short Term' if x is not None else None)
    sankey_df['price']=pd.cut(sankey_df['price'], bins=[-np.inf, 100, 300, 500, np.inf], labels=['<100', '100-300', '300-500', '>500']).astype(str)
    sankey_df['price']=sankey_df['price'].replace('nan', 'price_NA')
    sankey_df['host_is_superhost']=sankey_df['host_is_superhost'].fillna('superhost_NA')
    sankey_df['host_is_superhost']=sankey_df['host_is_superhost'].replace(['t', 'f'], ['superhost', 'not superhost'])

    sankey_df['all']='All Listing'
    sankey_df_grp=sankey_df.groupby(['all', 'neighbourhood_group', 'room_type', 'minimum_nights', 'price','host_is_superhost'])['id'].nunique().reset_index()

    layer_1_df=sankey_df_grp.groupby(['all', 'neighbourhood_group'])['id'].sum().reset_index()
    layer_1_df.columns=['source', 'target', 'value']

    layer_2_df=sankey_df_grp.groupby(['neighbourhood_group', 'room_type'])['id'].sum().reset_index()
    layer_2_df.columns=['source', 'target', 'value']

    layer_3_df=sankey_df_grp.groupby(['room_type', 'minimum_nights'])['id'].sum().reset_index()
    layer_3_df.columns=['source', 'target', 'value']

    layer_4_df=sankey_df_grp.groupby(['minimum_nights', 'price'])['id'].sum().reset_index()
    layer_4_df.columns=['source', 'target', 'value']

    layer_5_df=sankey_df_grp.groupby(['price', 'host_is_superhost'])['id'].sum().reset_index()
    layer_5_df.columns=['source', 'target', 'value']

    sankey_df_final=pd.concat([layer_2_df, layer_3_df, layer_4_df, layer_5_df])

    df_node = sankey_df_final.copy()
    # Get a list of all unique nodes
    unique_nodes = pd.concat([df_node['source'], df_node['target']]).unique()

    # Create a mapping from node names to indices
    node_mapping = {node: i for i, node in enumerate(unique_nodes)}

    # Use the mapping to transform the source and target columns to indices
    df_node['source'] = df_node['source'].map(node_mapping)
    df_node['target'] = df_node['target'].map(node_mapping)


    # Create the Sankey diagram
    sankey_fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=unique_nodes
        ),
        link=dict(
            source=df_node['source'],  # Source indices
            target=df_node['target'],  # Target indices
            value=df_node['value'],    # Flow values
        ))])

    # Update layout and show the plot
    sankey_fig.update_layout(title_text="Flow of listings to become Superhost-listings", 
                            font_size=12,
                            margin=dict(l=20, r=20, t=30, b=20), 
                            title=dict(x=0.01, y=0.97),
                            paper_bgcolor='aliceblue')

    
    m = folium.Map(location=[filtered_df['latitude'].median(), filtered_df['longitude'].median()], zoom_start=zoom, height='75%')
    FastMarkerCluster(data=filtered_df[['latitude', 'longitude']].values, 
                      #popups=[folium.Popup(row['name']) for _,row in filtered_df.iterrows()]
                      ).add_to(m)
    folium.LayerControl().add_to(m)
    map_html = m._repr_html_()
    
    # Room type distribution figure
    room_type_fig = px.pie(filtered_df, names='room_type', title='Room Type Distribution')
    room_type_fig.update_traces(textinfo='value+percent')
    room_type_fig.update_layout(font_size=12, margin=dict(l=20, r=20, t=40, b=20), title=dict(x=0.01, y=0.97), paper_bgcolor='aliceblue')    

    pop_roomtype = filtered_df.groupby('room_type')['id'].nunique().sort_values(ascending=False)
    pop_roomtype = ' and '.join(list(pop_roomtype.index)[:2])
    room_type_desc=html.Small([html.P(f"[INFO] Airbnb hosts have the option to offer various types of accommodations including entire homes or apartments, \
                                    private rooms, shared rooms, and, more recently, hotel rooms.The type of room and the manner in which it is managed \
                                    can make some Airbnb listings operate similarly to hotels, which can be disruptive for neighbors, reduce available housing, \
                                    and in some cases, contravene local laws."), 
                               html.P(f"[INSIGHTS] Most of the listings available are generally {pop_roomtype} in this area.")]) 

    # term_rentals figure
    if not term_type: 
        term_rentals_df = filtered_df.groupby('term_rentals')['id'].nunique().reset_index()
        term_rentals_df.columns=['Rental Term', 'count of listings']
        plot_title = 'Rental Term Distribution'
        text1="[ACTION]: Please Toggle 'Term of Rental' filter to see additional breakdown on Minimum number of nights"
        text2=""
        text3=""
    elif term_type=="Short Term":
        term_rentals_df = filtered_df.groupby('minimum_nights_bin')['id'].nunique().reset_index()
        term_rentals_df = term_rentals_df[term_rentals_df['minimum_nights_bin'].isin(['<=5', '5-10', '10-15', '15-20', '20-25', '25-30'])]
        term_rentals_df.columns=['Minimum Nights to book', 'count of listings']
        plot_title='{} Rentals Distribution'.format(term_type).lstrip()
        text1="[ACTION] Please Remove 'Term of Rental' filter to go back to seeing Overall Rental Term Distribution"
        (pl1, pl2) = (list(term_rentals_df[term_rentals_df['Minimum Nights to book']=='<=5']['count of listings'])[0],
                      term_rentals_df['Minimum Nights to book'][term_rentals_df['count of listings'].argmax()])
        text2 = f"[INSIGHTS] {pl1} listings have <5 Minimum nights policy. Majorly Listings have {pl2} nights as Minimum nights policy"
        text3 = f"[INFO] Airbnb's short-term rental policies often require hosts to register and obtain licenses, \
                adhere to occupancy and duration limits to prevent residential properties from becoming full-time vacation rentals, \
                and comply with local tax regulations. Safety standards, such as fire and health safety compliance, are also mandated in many jurisdictions. \
                These regulations aim to balance the interests of short-term rentals with community needs and safety."
    elif term_type=="Long Term":
        term_rentals_df = filtered_df.groupby('minimum_nights_bin')['id'].nunique().reset_index()
        term_rentals_df = term_rentals_df[~term_rentals_df['minimum_nights_bin'].isin(['<=5', '5-10', '10-15', '15-20', '20-25', '25-30'])]
        term_rentals_df.columns=['Minimum Nights to book', 'count of listings']
        plot_title='{} Term Rentals Distribution'.format(term_type).lstrip()
        text1="[ACTION] Please Remove 'Term of Rental' filter to go back to seeing Overall Rental Term Distribution"
        (pl1,pl2) = (list(term_rentals_df['Minimum Nights to book'])[term_rentals_df['count of listings'].argmax()],
                    term_rentals_df[~term_rentals_df['Minimum Nights to book'].isin(['30-60', '60-90', '90-120', '120-150', '150-180'])]['count of listings'].sum())
        text2 = f"[INSIGHTS] Majorly Listings have {pl1} nights as Minimum nights policy. {pl2} listings have more than 6m as Minimum nights Policy"
        text3 = f"[INFO] Airbnb's long-term rental policies include a modified payment structure where guests pay monthly instead of upfront, \
                  making financial management easier and more akin to traditional leasing. \
                  Cancellation policies for these rentals require a 30-day notice, providing security for both parties \
                  but also imposing a potential cost on guests who cancel mid-stay. \
                  Additionally, compliance with local housing regulations, potential requirements for lease agreements, \
                  and adherence to safety and maintenance standards ensure that long-term stays align with both Airbnb's guidelines and local laws."
    term_rentals_df['Percentage']=((term_rentals_df['count of listings']/term_rentals_df['count of listings'].sum())*100).round(1)
    term_rentals= px.bar(term_rentals_df, x=term_rentals_df.columns[0], y=term_rentals_df.columns[1], title=plot_title, text=term_rentals_df['Percentage'])
    term_rentals.update_traces(texttemplate='%{text}%', textposition='outside')
    term_rentals.update_layout(font_size=12, margin=dict(l=20, r=20, t=40, b=20), title=dict(x=0.01, y=0.97), paper_bgcolor='aliceblue')
    
    term_rentals_desc=html.Small([html.P(text1),
                                  html.P(text2),
                                  html.P(text3)])

    # booking last 12m figure
    last_12m_availability_df=filtered_df.groupby('last_1yr_availability')['id'].nunique().reset_index()
    last_12m_availability_df.columns=['No. of Days booked in last 365 Days', 'count of listings']
    last_12m_availability_df['Percentage']=((last_12m_availability_df['count of listings']/last_12m_availability_df['count of listings'].sum())*100).round(1)
    #last_12m_availability = px.bar(last_12m_availability_df, x=last_12m_availability_df.columns[0], y=last_12m_availability_df.columns[1], title='Last 365 Days availability', text=last_12m_availability_df['Percentage'])
    #last_12m_availability.update_traces(texttemplate='%{text}%', textposition='outside')
    #last_12m_availability.update_layout(font_size=12, margin=dict(l=20, r=20, t=40, b=20), title=dict(x=0.01, y=0.97), paper_bgcolor='aliceblue')

    # Average Earnings based on last 12 Months availability
    average_earnings_df=(filtered_df.groupby('last_1yr_availability')['price'].sum()/filtered_df.groupby('last_1yr_availability')['id'].nunique()).reset_index()
    average_earnings_df.columns=['No. of Days booked in last 365 Days', 'Average Earnings in Dollars']

    # Total Earnings 
    total_earnings_df=filtered_df.copy()
    total_earnings_df['price']=total_earnings_df['price']*(365-total_earnings_df['availability_365'])
    total_earnings_df=total_earnings_df.groupby('last_1yr_availability')['price'].sum().reset_index()
    total_earnings_df.columns=['No. of Days booked in last 365 Days', 'Total Earnings in Dollars']


    # Dual axis figure for last_12m_availability and average_earnings
    last_12m_availability = make_subplots(specs=[[{"secondary_y": True}]])

    # Add bar chart to the figure on the primary y-axis
    last_12m_availability.add_trace(
        go.Bar(
            x=last_12m_availability_df[last_12m_availability_df.columns[0]], 
            y=last_12m_availability_df[last_12m_availability_df.columns[1]], 
            text=last_12m_availability_df['Percentage'],
            texttemplate='%{text}%', 
            textposition='outside',
            hoverinfo='name+x+y',
            name='Listings'
        ),
        secondary_y=False  # Indicates that this goes on the first y-axis
    )

    # Add line chart to the figure on the secondary y-axis
    if view_avg_total=='Show Average Earnings':

        last_12m_availability.add_trace(
            go.Scatter(
                x=average_earnings_df[average_earnings_df.columns[0]][1:], 
                y=average_earnings_df[average_earnings_df.columns[1]][1:],
                name='Earnings',
                mode='lines+markers',
                text = [f'Average: {format_number(i)}, Total: {format_number(j)}' for i,j in zip(average_earnings_df['Average Earnings in Dollars'][1:], total_earnings_df['Total Earnings in Dollars'][1:])],
                hoverinfo='text+name'
            ),
            secondary_y=True  # Indicates that this goes on the second y-axis
        )
        # Set primary y-axis title
        last_12m_availability.update_yaxes(title_text='count of listings', secondary_y=False)

        # Set secondary y-axis title
        last_12m_availability.update_yaxes(title_text='Earnings per night in Dollars', secondary_y=True)

        plot_title='Last 365 Days availability and Average Earnings per night'
    
    elif view_avg_total=='Show Total Earnings':

        last_12m_availability.add_trace(
            go.Scatter(
                x=total_earnings_df[total_earnings_df.columns[0]][1:], 
                y=total_earnings_df[total_earnings_df.columns[1]][1:],
                name='Earnings',
                mode='lines+markers',
                text = [f'Average: {format_number(i)}, Total: {format_number(j)}' for i,j in zip(average_earnings_df['Average Earnings in Dollars'][1:], total_earnings_df['Total Earnings in Dollars'][1:])],
                hoverinfo='text+name'
            ),
            secondary_y=True  # Indicates that this goes on the second y-axis
        )
        # Set primary y-axis title
        last_12m_availability.update_yaxes(title_text='count of listings', secondary_y=False)

        # Set secondary y-axis title
        last_12m_availability.update_yaxes(title_text='Total Earnings in Dollars', secondary_y=True)

        plot_title='Last 365 Days availability and Total Earnings'


    # Set x-axis title
    last_12m_availability.update_xaxes(title_text='No. of Days booked in last 365 Days')

    
    # Set chart title
    last_12m_availability.update_layout(title_text=plot_title, 
                                        margin=dict(l=20, r=20, t=40, b=20), 
                                        title=dict(x=0.01, y=0.97), 
                                        paper_bgcolor='aliceblue',
                                        legend=dict(x=0.8,y=-0.4)
                                        )

    last_12m_availability_desc=html.Small([html.P("[ACTION] Toggle filter below the chart to switch between viewing 'Average Earnings' and 'Total Earnings'. Total Earnings is actually overall earning of the cohort. Calculated by (Price_per_night)*(number_of_night_booked)"),
                                            html.P("[ACTION] Check Average earnings per night for different cohorts by toggling filters."),
                                            html.P("[INFO] Booking data can highlight demand trends, \
                                                  showing when and where properties are most sought after. \
                                                  A high number of days booked suggests strong market demand or \
                                                  less strict local rental regulations, while properties with fewer \
                                                  bookings might indicate overpricing or a saturated market. \
                                                  A prevalence of heavily booked listings may point to professional \
                                                  hosting operations rather than individual hosts.\
                                                  By correlating availability with earnings, \
                                                  hosts can optimize pricing to maximize revenue during peak demand periods."),
                                            ]) 

    
    #price distribution figure
    price_distribution_df=filtered_df.groupby('price_bin')['id'].nunique().reset_index()
    price_distribution_df.columns=['Price in Dollars', 'count of listings']
    price_distribution_df['Percentage']=((price_distribution_df['count of listings']/price_distribution_df['count of listings'].sum())*100).round(1)
    price_distribution = px.bar(price_distribution_df, x=price_distribution_df.columns[0], y=price_distribution_df.columns[1], title='Price Distribution', text=price_distribution_df['Percentage'])
    price_distribution.update_traces(texttemplate='%{text}%', textposition='outside')
    price_distribution.update_layout(font_size=12, margin=dict(l=20, r=20, t=40, b=20), title=dict(x=0.01, y=0.97), paper_bgcolor='aliceblue')

    price_distribution_desc=html.Small([html.P("[INFO] Price distribution data can reveal pricing \
                                               trends and market segmentation, helping to identify budget, mid-range, \
                                               and luxury accommodations. Competitive analysis through price distribution helps \
                                               hosts adjust their rates competitively. \
                                               Over time, this can uncover long-term trends in regional \
                                               attractiveness and market dynamics."
                                               )]) 

    # Average Price based on Neighbourhood
    if filtered_df['neighbourhood_group'].nunique()>1:
        top_nb_price_df=filtered_df.groupby('neighbourhood_group')['price'].median().reset_index()
        top_nb_price_df.columns=['Neighood Group','Price in Dollars']
        text1="[ACTION] Select a neighbourhood group from 'Area' Filter to see median prices for areas in the Neighbourhood."
    else:
        top_nb_price_df=filtered_df.groupby('neighbourhood')['price'].median().reset_index()
        top_nb_price_df.columns=['Neighood Area','Price in Dollars']
        if len(nb_ls)>1:
            pl=nb_ls[0]
            text1=f"""[ACTION] Select '{pl}' from 'Area' filter to switch back to comparing prices of all areas from {pl} neighbourhood"""
        else:
            text1=""

    top_nb_price_df=top_nb_price_df.sort_values('Price in Dollars', ascending=True)
    
    top_nb_price = px.bar(top_nb_price_df, x=top_nb_price_df.columns[0], y=top_nb_price_df.columns[1], title='Area-wise Median Price', width=None)
    top_nb_price.update_layout(font_size=12, margin=dict(l=20, r=20, t=40, b=20), title=dict(x=0.01, y=0.97), paper_bgcolor='aliceblue')

    
    top_nb_price_desc=html.Small([html.P(text1),
                                  html.P("[INFO] Area-wise median price analysis for listings can highlight regional pricing benchmarks, \
                                         helping travelers and hosts make informed decisions about lodging costs. \
                                         These prices can also reflect the economic health and desirability of different areas, \
                                         influencing real estate valuations and investment opportunities. \
                                         Comparisons across regions can reveal market saturation or untapped opportunities, \
                                         guiding new hosts on where to establish their listings competitively. \
                                         ")]) 
    
    # Stats output
    stats =  dbc.Row([html.H4("General Statistics", className="text-center"),
             dbc.Col([html.H6(f"Total Listings", className="text-center"), html.P(f"{len(filtered_df)}", className="text-center")]),
             dbc.Col([html.H6(f"Average Price", className="text-center"), html.P(f"${filtered_df['price'].mean():.2f}", className="text-center")]),
             dbc.Col([html.H6(f"Median Price", className="text-center"), html.P(f" ${filtered_df['price'].median():.2f}", className="text-center")])
            ])
    
    
    

    return map_html, \
            room_type_fig, \
            stats, \
            term_rentals, \
            last_12m_availability, \
            price_distribution, \
            top_nb_price, \
            room_type_desc, \
            term_rentals_desc, \
            last_12m_availability_desc, \
            price_distribution_desc, \
            top_nb_price_desc, \
            sankey_fig, \
            sankey_fig
# add folium markers as in openairbnb data
# add all the dynamic place holder text
# add dashboard descripts
# add how to use dashboard
# host flask app.

if __name__ == '__main__':
    app.run_server(debug=True)
