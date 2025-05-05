import numpy as np
import streamlit as st
import glob

from astropy import wcs
from astropy.io import fits
from bokeh.plotting import figure
from bokeh.models import LinearColorMapper, ScaleBar, Metric, Range1d, CustomJS, ColumnDataSource, LabelSet, LinearAxis
from streamlit_bokeh import streamlit_bokeh

from bokeh.layouts import gridplot
from bokeh.models import CrosshairTool, Span

import matplotlib

def drawContours(contstart=None,contend=None,contnoise=None):
    poscontours = np.geomspace(contstart,contend, num=5)
    negcontours=poscontours[::-1]*(-1.0)
    contours=np.concatenate((negcontours,poscontours))*contnoise
    
    return contours


def plot_figure(file_path, color_map, z_value, crosshair_width, crosshair_height, minval=None, maxval=None, contour_x=None, contour_y=None, contour_data=None, x_range=None, y_range=None, extra_x_range=None):
    hdul = fits.open(file_path)
    img =hdul[0]
    w = wcs.WCS(img.header, hdul)
    header = img.header

    pixel_size = - header['cdelt1']*3600.
    full_size = np.floor(len(img.data[0])*pixel_size)

    bmaj_asec = header['bmaj']*3600
    bmin_asec = header['bmin']*3600
    bpa = header['bpa']

    y = np.linspace(-full_size/2, full_size/2, img.data.shape[0])
    x = np.linspace(-full_size/2, full_size/2, img.data.shape[1])

    if minval == None and maxval == None:
        minval, maxval = np.nanpercentile(img.data, (0., 100.))

    mapper = LinearColorMapper(palette=color_map,low=minval, high=maxval, nan_color='white')

    p = figure(width=450, height=450, x_axis_label=r'$$\Delta \text{ R.A. (arcsec)}$$', y_axis_label=r'$$\Delta \text{ Dec. (arcsec)}$$', tooltips=[("x", "$x"), ("y", "$y"), z_value])
    p.x_range.range_padding = p.y_range.range_padding = 0

    if x_range == None:
        p.x_range = Range1d(-7.5, 7.5)
        p.y_range = Range1d(-7.5, 7.5)
    else:
        p.x_range = x_range
        p.y_range = y_range
    
    if extra_x_range == None:
        p.extra_x_ranges = {"foo": Range1d(start=-7.5*151, end=7.5*151)}
    else:
        p.extra_x_ranges = extra_x_range

    p.add_layout(LinearAxis(x_range_name="foo", visible=False), 'above')


    p.image(image=[img.data], x=x[0], y=y[0], dw=x[-1]-x[0], dh=y[-1]-y[0], color_mapper=mapper)#, dw=10, dh=10, palette="Spectral11", level="image")

    # Add a scale bar
    scale_bar = ScaleBar(
    range=p.extra_x_ranges['foo'],
    unit="au",
    dimensional=Metric(base_unit='au', exclude=['dau','cau','mau','hau','kau']),
    orientation="horizontal",
    location="top_right",
    label="@{value}{%.2f} @{unit}",  # Disable default label
    bar_length=50,
    bar_line_width=2,
    background_fill_alpha=0.8,
    )
    p.add_layout(scale_bar)

    if contour_data is not None:
        contours=drawContours(5, 405, 1.8528968e-05)
        p.contour(contour_x, contour_y, contour_data, contours, line_color="black")


    p.add_tools(CrosshairTool(overlay=[crosshair_width, crosshair_height]))

    return p

def main():
    st.set_page_config(page_title= 'eDisk Spectral Plots', page_icon='eDisk_logo_ver.4.jpg',layout="wide")

    molecules=['12CO', '13CO', 'C18O', 'DCN', 'CH3OH', 'SiO', 
             'SO', 'H2CO_3_03-2_02_218.22GHz', 
             'H2CO_3_21-2_20_218.76GHz',  
             'H2CO_3_22-2_21_218.47GHz',
             'C3H2_217.82',
             'C3H2_217.94',
             'C3H2_218.16']


    mom8_imgs = glob.glob('*robust_2.0_mom8_15arcsec.fits')
    mom9_imgs = glob.glob('*robust_2.0_mom9_15arcsec.fits')
    
    mol=st.sidebar.selectbox('Select the molecule:',molecules)
    mom8_idx = [i for i, s in enumerate(mom8_imgs) if mol in s][0]
    mom9_idx = [i for i, s in enumerate(mom9_imgs) if mol in s][0]
    mom8_img = mom8_imgs[mom8_idx]
    mom9_img = mom9_imgs[mom9_idx]

    cmap = matplotlib.colormaps['Spectral']
    hex_vals = [matplotlib.colors.rgb2hex(cmap(i)) for i in range(cmap.N)]

    cmap2 = matplotlib.colormaps['RdBu']
    hex_vals2 = [matplotlib.colors.rgb2hex(cmap2(i)) for i in range(cmap2.N)]

    crosshair_width = Span(dimension="width", line_dash="dashed", line_width=2)
    crosshair_height = Span(dimension="height", line_dash="dotted", line_width=2)

    cont_img = 'CB68_SBLB_continuum_robust_2.0.pbcor.tt0.fits'

    with fits.open(cont_img) as cont_hdul:
        cont_img_data = cont_hdul[0].data
        header = cont_hdul[0].header

        pixel_size = - header['cdelt1']*3600.
        full_size = len(cont_img_data)*pixel_size
        y = np.linspace(-full_size/2, full_size/2, cont_img_data.shape[0])
        x = np.linspace(-full_size/2, full_size/2, cont_img_data.shape[1])

        xx, yy = np.meshgrid(x,y)

        print(full_size)
    #p1 = plot_figure(cont_img, 'Inferno256', ("Intensity", "@image Jy/beam"), crosshair_width, crosshair_height)
    p2 = plot_figure(mom8_img, hex_vals[::-1], ("Intensity", "@image Jy/beam"), crosshair_width, crosshair_height, contour_x = xx, contour_y = yy, contour_data = cont_img_data)
    #p3 = plot_figure(mom9_img, hex_vals2[::-1], ("Velocity", "@image km/s"), crosshair_width, crosshair_height, contour_x = xx, contour_y = yy, contour_data = cont_img_data, x_range = p2.x_range, y_range = p2.y_range, extra_x_range = p2.extra_x_ranges)

    p_all = gridplot([[p2]], toolbar_location='right')

    streamlit_bokeh(p_all, use_container_width=True)

if __name__=='__main__':
    main()