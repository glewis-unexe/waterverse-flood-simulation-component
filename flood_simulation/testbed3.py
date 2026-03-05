import unexecore.ascfile

def asc_get_info(asc_file: unexecore.ascfile.ASCFile) -> dict:
    info = {}
    try:
        for y in range(0, asc_file.nrows):
            for x in range(0, asc_file.ncols):
                try:
                    v0 = asc_file.data[y][x]

                    if v0 != asc_file.nodata:
                        if v0 not in info:
                            info[v0] = 0
                        info[v0] += 1

                except Exception as e:
                    print(unexecore.debug.exception_to_string(e))
    except Exception as e:
        print(unexecore.debug.exception_to_string(e))

    return info


filename = '/home/gareth/Documents/dev/work/waterverse/for-forking/waterverse-flood-simulation-component/flood_simulation/output/current/current_WDrasterParam_PEAK.asc'
#filename = '/home/gareth/Documents/dev/work/waterverse/for-forking/waterverse-flood-simulation-component/wdme_flood_component/sim_output/current/current_WDrasterParam_PEAK.asc'
asc_file = unexecore.ascfile.ASCFile()
asc_file.load(filename)
info = asc_get_info(asc_file)

print()
