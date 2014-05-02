import sublime, sublime_plugin
import re 

from pprint import pprint

# This finds the entity around the current cursor/selection and parses out the name, generics, and ports
def parseEntity(view):
    entityReg = None
    genericListReg = None
    portListReg = None

    regionList=view.find_by_selector('meta.block.entity.vhdl')

    print("Regionlist:("+str(regionList)+")")

    mainSel = view.sel()[0]
    print("Selection: "+str(mainSel))
    view.sel().clear()
    for r in regionList:
        
        if r.contains(mainSel):#mainSel.contains(r):
            
            view.sel().clear()
            view.sel().add(r)
            entityReg = r
            entityText = view.substr(r)
            entityName=re.search(r"(?i)entity\s*(\w+)\s",entityText).group(1)
            print("Name: "+entityName)

    generic_elements = [r for r in view.find_by_selector('source.vhdl meta.block.entity.vhdl meta.block.generic_list.vhdl meta.block.parenthetical_list.vhdl meta.list.element.vhdl') if entityReg.contains(r)]
    port_elements = [r for r in view.find_by_selector('source.vhdl meta.block.entity.vhdl meta.block.port_list.vhdl meta.block.parenthetical_list.vhdl meta.list.element.vhdl') if entityReg.contains(r)]


    parse_generic_element_re = r"(?i)(\w+)\s*:\s*(\w+)\s*(:=\s*(.*))?\s*[;)]\Z"
    parse_port_element_re = r"(?i)(\w+)\s*:\s*(IN|OUT|INOUT|BUFFER)\s*(.*)\s*(:=\s*(.*)\s*)?[;)]\Z" # eventually add assignment...

    generics = []
    for g in generic_elements:
        gstr=view.substr(g)
        gstr=gstr.replace("\n"," ").replace("\r"," ").replace("\t"," ").strip()
        matchObj=re.match(parse_generic_element_re,gstr)
        if matchObj != None:
            pprint(matchObj.groups())
            gname = matchObj.group(1)
            gtype = matchObj.group(2)            
            gdefault = matchObj.group(4)
            if gdefault != None:
                gdefault = gdefault.strip()
            #print("Generic: "+str(g)+"  ["+gname+"|"+gtype+"|"+str(gdefault)+"]")
            generics.append( (gname,gtype,gdefault) )
            

    ports = []
    for p in port_elements:
        pstr=view.substr(p)
        pstr=pstr.replace("\n"," ").replace("\r"," ").replace("\t"," ").strip()
        matchObj=re.match(parse_port_element_re,pstr)
        if matchObj != None:
            pname=matchObj.group(1)
            pdir=matchObj.group(2)
            ptype=matchObj.group(3).strip()
            pdefault=matchObj.group(5)
            if pdefault != None:
                pdefault=pdefault.strip()
            ports.append( (pname, pdir, ptype, pdefault) ) # name, direction, type, default value (or None)
    return (entityName,generics,ports)



def genComponent(name,generics,ports):
    out="  component "+name+"\n"
    if len(generics)>0:
        out=out+"    generic (\n"
        for g in generics:
            out=out+"      "+g[0]+" : "+g[1]
            if g[2] != None:
                out=out+" := "+g[2]
            out=out+";\n"
        out=out[0:-2]+");\n" # replace ; with );
    if len(ports)>0:
        out=out+"    port (\n"
        for p in ports:
            out=out+"      "+p[0]+" : "+p[1]+" "+p[2]
            if p[3] != None:
                out=out+" := "+p[3]
            out=out+";\n"
        out=out[0:-2]+");\n" # replace ; with );
    out = out + "  end component "+name+";\n\n"
    return out

def genInstance(name,generics,ports):
    out="  "+name+"_inst : "+name+"\n"
    if len(generics)>0:
        out=out+"    generic map (\n"
        for g in generics: # we'll map the generics to symbols of the same name to support passing generics through hierarchies...an alternate implementation might map them to their default values
            out=out+"      "+g[0]+" => "+g[0]
            out=out+",\n"
        out=out[0:-2]+")\n" # replace , with )
    if len(ports)>0:
        out=out+"    port map (\n"
        for p in ports:
            out=out+"      "+p[0]+" => "+p[0]
            if p[3] != None:
                out=out+" := "+p[3]
            out=out+",\n"
        out=out[0:-2]+");  --"+p[2]+"\n\n" # replace , with );
    return out




def genSignals(name,generics,ports):
    out = "  -- signals for "+name+"-----------------\n"
    if len(ports)>0:
        for p in ports:
            out=out+"  signal "+p[0]+" : "+p[2]
            if p[3] != None:
                out=out+" := "+p[3]
            out=out+";\n"
    out = out + "  -- end signals for "+name+"\n\n"
    return out


def vhdl_to_sv_type(typestr):
    svtype =""
    svarray = ""
    rangeRE = r'\(([0-9]+)[^0-9]*to[^0-9]*([0-9]+)\)'
    svarray = " ".join([ "["+ b[0]+":"+b[1]+"]" for b in re.findall(rangeRE,typestr.lower())])
    tempstr = re.sub(rangeRE,"",typestr.lower())
    if tempstr.lower() == "std_logic":
        return ('logic','')
    elif tempstr.lower().startswith("std_logic_vector"):
        svtype='logic'
        return svtype,svarray
    # no special case, so just pass it through...
    return (tempstr,svarray)

def genSVModule(name,generics,ports):
    out="module "+name+"\n"
    if len(generics)>0:
        out=out+"  #(\n"
        for g in generics:
            #out=out+"      "+g[0]+" : "+g[1]

            if g[2] != None:
                out = out + "    "+g[0]+" = "+g[2]
                #out=out+" := "+g[2]
            out=out+",\n"
        out=out[0:-2]+")\n" # replace ,\n with )
    if len(ports)>0:
        out=out+"  (\n"
        for p in ports:
            #out=out+"      "+p[0]+" : "+p[1]+" "+p[2]
            direction = ""
            if "in" in p[1].lower():
                direction = "input"
            if "out" in p[1].lower():
                direction = "output"
            if "inout" in p[1].lower() or "buffer" in p[1].lower():
                direction = "inout"
            (svtype,svarray) = vhdl_to_sv_type(p[2])
            out=out+"    "+direction+" "+svtype+" "+svarray+" "+p[0]
            if p[3] != None:
                out=out+" = "+p[3]
            out=out+",\n"
        out=out[0:-2]+"\n  );\n" # replace , with );
    #out = out + "  end component "+name+";\n\n"
    out = out + "\nendmodule\n"
    return out

def genSVInstance(name,generics,ports):
    out=name+" "
    if len(generics)>0:
        out=out+"  #("
        for g in generics:
            #out=out+"      "+g[0]+" : "+g[1]
            out = out + " ."+g[0]+"("
            if g[2] != None:
                out=out+g[2]
                #out=out+" := "+g[2]
            out=out+"), "
        out=out[0:-2]+")" # replace ", " with ")"
    out = out + " "+ name+"_inst \n"
    if len(ports)>0:
        out=out+"  (\n"
        for p in ports:
            #out=out+"      "+p[0]+" : "+p[1]+" "+p[2]
            direction = ""
            if "in" in p[1].lower():
                direction = "input"
            if "out" in p[1].lower():
                direction = "output"
            if "inout" in p[1].lower() or "buffer" in p[1].lower():
                direction = "inout"
            (svtype,svarray) = vhdl_to_sv_type(p[2])
            comment = "//"+direction+" "+svtype+" "+svarray
            out=out+"    ."+p[0]+"("+p[0]+"), "+comment+"\n"
            #if p[3] != None:
            #    out=out+" = "+p[3]
            #out=out+",\n"
        out=out[0:-(len(comment)+3)]+" "+comment+"\n  );\n" # replace ', // comment\n' with );
    return out


class VhdlCopyAsComponentCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        (name,generics,ports) = parseEntity(self.view)
        sublime.set_clipboard(genComponent(name,generics,ports))
        sublime.status_message("VHDL Entity "+name+" copied as component")

class VhdlCopyAsInstanceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        (name,generics,ports) = parseEntity(self.view)
        sublime.set_clipboard(genInstance(name,generics,ports))
        sublime.status_message("VHDL Entity "+name+" copied as instance")

class VhdlCopyAsSignalsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        (name,generics,ports) = parseEntity(self.view)
        sublime.set_clipboard(genSignals(name,generics,ports))
        sublime.status_message("VHDL Entity "+name+" copied as signals")


class VhdlCopyAsSvModuleCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        (name,generics,ports) = parseEntity(self.view)
        sublime.set_clipboard(genSVModule(name,generics,ports))
        sublime.status_message("VHDL Entity "+name+" copied as SV module")

class VhdlCopyAsSvInstanceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        (name,generics,ports) = parseEntity(self.view)
        sublime.set_clipboard(genSVInstance(name,generics,ports))
        sublime.status_message("VHDL Entity "+name+" copied as SV instance")


class VhdlBeautifyCommand(sublime_plugin.TextCommand):
    def run(self, edit):   
        sublime.status_message("Beautify VHDL NOT YET SUPPORTED")


class VhdlSelCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        (name,generics,ports) = parseEntity(self.view)
        #print "=== GENERICS:"
        #pprint(generics)
        #print
        #print "=== PORTS:"
        #pprint(ports)

        sublime.set_clipboard(genComponent(entityName,generics,ports))

        return # skip the extra buffer
        wnd = self.view.window()
        scratch = wnd.new_file()
        wnd.focus_view(scratch)
        scratch.set_scratch(True)
        #scratch.insert(edit,scratch.size(),"======\nENTITY:\n"+entityText+"\n")
        scratch.insert(edit,scratch.size(),"======\nGENERICS:\n"+"\n".join([self.view.substr(r) for r in generic_elements])+"\n")
        scratch.insert(edit,scratch.size(),"======\nPORT LIST:\n"+"\n".join([self.view.substr(r) for r in port_elements])+"\n")



        #mainSel=self.view.sel()[0]
        #self.view.sel().clear()
        #self.view.sel().add(mainSel)
        #sublime.status_message("starting loop")
        #while not selContainsStr(self.view,self.view.sel()[0],"entity"):
        #   print self.view.sel() 
        #   self.view.sel().add(self.view.extract_scope(self.view.sel()[0].end()))
