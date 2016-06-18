import json

cal = {}
with open("surf_calibrations.json","r") as infile:
    cal = json.load(infile)

def save_vadjn(dna, vadjn):
    for key in cal:
        if cal[key]['DNA'] == dna:
            print "Saving VadjN for board %s" % key
            board_cal = cal[key]
            board_cal['vadjn'] = vadjn
            with open("surf_calibrations.json","w") as outfile:
                json.dump(cal, outfile)
    print "No board found with DNA %x" % dna            
    
def read_vadjn(dna):
    for key in cal:
        if cal[key]['DNA'] == dna:
            board_cal = cal[key]
            if 'vadjn' in board_cal:
                return board_cal['vadjn']
            else:
                return None
    return None

def add_board(serial, dna):
    cal[serial] = dna
    with open("surf_calibrations.json","w") as outfile:
        json.dump(cal, outfile)