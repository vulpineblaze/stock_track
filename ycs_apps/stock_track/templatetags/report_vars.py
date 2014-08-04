from django import template

register = template.Library()

@register.simple_tag
def fill_line_graph_with_company(the_company):
    """ """
    
    ret_string = ""
    
    for item in the_company.daily_set.all():
        date_string = " new Date("+str(item.date.year)+","+str(item.date.month-1)+","+str(item.date.day)+")"
        ret_string += ",["+date_string+","
        ret_string += ""+str(item.price_open)+","
        ret_string += ""+str(item.price_close)+","
        ret_string += ""+str(item.price_high)+","
        ret_string += ""+str(item.price_low)+","
        #~ ret_string += ""+str(item.price_volume)+","
        ret_string += ""+str(item.price_adj_close)+"]"
        
    #~ test_string = ",['2014-04-15','55','55','55','55','55','55']"
    #~ test_string = date_string
    return ret_string[1:]  #test_string#ret_string
