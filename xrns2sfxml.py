#!/usr/bin/python
from datetime import date
from subprocess import call
import aifc, array, chunk, datetime, logging, math, os, os.path
import struct, sys, tempfile, wave, xml.dom.minidom
from xml.dom import minidom
from xml.dom.minidom import Document
import zipfile

# init sf2 xml
sf2doc = Document()
instruments = sf2doc.createElement('instruments')
presets = sf2doc.createElement('presets')
wavetables = sf2doc.createElement('wavetables')

def PrintUsage():
  UsageStr = 'xrns2sfxml version \n\n\n' + """
Usage: xrns2sfxml [song.xrns] > out.xml 
"""
  print UsageStr
  sys.exit(0)

def initSf2XML(name):
    pysf        = sf2doc.createElement('sf:pysf')
    pysf.attributes['version'] = '2'
    pysf.attributes['xmlns:sf'] = "http://terrorpin.net/~ben/docs/alt/music/soundfont/pysf"
    pysf.attributes['xmlns:xsi'] = "http://www.w3.org/2001/XMLSchema-instance"
    pysf.attributes['xsi:schemaLocation'] = "http://terrorpin.net/~ben/docs/alt/music/soundfont/pysf pysf.xsd"
    sf2         = sf2doc.createElement('sf2')
    sf2.appendChild( createTextNode(sf2doc,'ICRD',date.today().strftime("%A %d. %B %Y") ) )
    sf2.appendChild( createTextNode(sf2doc,'INAM',name) )
    sf2.appendChild( createTextNode(sf2doc,'ISFT','xrns2sfxml') )
    sf2.appendChild( createTextNode(sf2doc,'IPRD','LEONDUSTAR') )
    sf2.appendChild( createTextNode(sf2doc,'ISNG','MADFUNKY') )
    sf2.appendChild(instruments)
    sf2.appendChild(presets)
    sf2.appendChild(wavetables)
    pysf.appendChild(sf2)
    sf2doc.appendChild(pysf)
   
def convertSamples():
    path = os.path.dirname(os.path.realpath(__file__))
    script = "/xrns2sfxml.sh"
    call([path+script,"dir2wav","/tmp/SampleData"])


def unzip(file,destdir):
    call(["rm","-rf","/tmp/SampleData"])
    call(["rm","-rf","/tmp/Song.xml"])
    zip_ref = zipfile.ZipFile( file, 'r')
    zip_ref.extractall(destdir)
    zip_ref.close()

def createTextNode(doc,tag,text):
    el = doc.createElement(tag)
    el.appendChild( sf2doc.createTextNode( str(text) ) )
    return el

def convert(Src, Dst):
    unzip(Src,'/tmp')
    convertSamples()
    rnsdoc = minidom.parse('/tmp/Song.xml')
    itemlist = rnsdoc.getElementsByTagName('Instrument')
    initSf2XML(Src)
    #print(len(itemlist))
    #print(itemlist[0].attributes['name'].value)
    instrumentn = 1
    samplen = 1
    sampleDict = {}

    for rnsinstrument in itemlist:
        instrument = sf2doc.createElement('instrument')
        zones      = sf2doc.createElement('zones')
        iname   = rnsinstrument.getElementsByTagName('Name')[0].firstChild.nodeValue
        samples = rnsinstrument.getElementsByTagName('Sample')
        if( samples.length == 0) :
            continue
        for sample in samples:
            # /tmp/SampleData/Instrument00 (Hat-002)
            # /tmp/SampleData/Instrument00 (Hat-002)/Sample00 (Hat-002).flac
            # /tmp/SampleData/Instrument00 (Hat-002)/Sample01 (Kick-005).flac
            sf2Sample = sf2doc.createElement('wavetable')

            sname = sample.getElementsByTagName('Name')[0].firstChild.nodeValue
            sampleDict[sname] = samplen
            sname_parens = '('+sname+')'
            iname_parens = '('+iname+')'
            filename = '/tmp/SampleData/Instrument' + format(instrumentn-1,'02') + ' '
            filename += iname_parens + '/Sample' + format(samplen-1,'02') + ' ' + sname_parens + ".wav"
            sf2Sample.appendChild( createTextNode(sf2doc,'file', filename) )
            sf2Sample.appendChild( createTextNode(sf2doc,'id', samplen) )
            sf2Sample.appendChild( createTextNode(sf2doc,'name',sname) )
            sf2Sample.appendChild( createTextNode(sf2doc,'pitch',69) )

            loopmode  = sample.getElementsByTagName('LoopMode')[0].firstChild.nodeValue
            if( loopmode != "Off" ):
                loop      = sf2doc.createElement('loop')
                lbegin    = sample.getElementsByTagName('LoopStart')[0].firstChild.nodeValue
                lend      = sample.getElementsByTagName('LoopEnd')[0].firstChild.nodeValue
                loop.appendChild( createTextNode(sf2doc,'begin',lbegin ) )
                loop.appendChild( createTextNode(sf2doc,'end',lend ) )
                sf2Sample.appendChild(loop)
                

            wavetables.appendChild(sf2Sample)

            # but also add a zone for it *TODO* duplicate when stereo 
            zone     = sf2doc.createElement('zone')
            keyrange = sf2doc.createElement('keyRange')
            begin    = sample.getElementsByTagName('NoteStart')[0].firstChild.nodeValue
            end      = sample.getElementsByTagName('NoteEnd')[0].firstChild.nodeValue
            root     = sample.getElementsByTagName('BaseNote')[0].firstChild.nodeValue
            sname = sample.getElementsByTagName('Name')[0].firstChild.nodeValue
            keyrange.appendChild( createTextNode(sf2doc,'begin',begin) )
            keyrange.appendChild( createTextNode(sf2doc,'end',end) )
            zone.appendChild( createTextNode(sf2doc,'overridingRootKey', root) )
            zone.appendChild(keyrange)
            zone.appendChild( createTextNode(sf2doc,'wavetableId',samplen) )
            zones.appendChild(zone)
            samplen += 1


        # create instrument
        instrument.appendChild( createTextNode(sf2doc,'id', instrumentn) )
        instrument.appendChild( createTextNode(sf2doc,'name',iname) )
        instrument.appendChild( zones )
        instruments.appendChild(instrument)

        # create preset
        preset = sf2doc.createElement('preset')
        preset.appendChild( createTextNode(sf2doc,'bank',0) )
        preset.appendChild( createTextNode(sf2doc,'id', instrumentn) )
        preset.appendChild( createTextNode(sf2doc,'name', iname) )
        pzones      = sf2doc.createElement('zones')
        pzone       = sf2doc.createElement('zone')
        pzone.appendChild( createTextNode(sf2doc,'instrumentId',instrumentn) )
        pkeyrange   = sf2doc.createElement('keyRange')
        pkeyrange.appendChild( createTextNode(sf2doc,'begin',0) )
        pkeyrange.appendChild( createTextNode(sf2doc,'end',127) )
        pzone.appendChild(pkeyrange)
        pzones.appendChild( pzone )
        preset.appendChild( pzones )
        presets.appendChild(preset)

        instrumentn=instrumentn+1

    #print (sf2doc.toprettyxml(indent='\t'))   
    OutHandle = open(Dst, 'wb')
    OutHandle.write(sf2doc.toprettyxml(indent='\t'))
    OutHandle.close()

if __name__ == '__main__':
  if len(sys.argv) != 3:       PrintUsage()
  convert( sys.argv[1], sys.argv[2] )
