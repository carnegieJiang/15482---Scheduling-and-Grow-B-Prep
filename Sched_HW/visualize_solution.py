import matplotlib.pyplot as plt

def wait_for_input():
    plt.pause(0.25)
    try: input("waiting, press enter to continue: ")
    except: pass

def plot_intervals(row_list, num_cols, diffjobs, solution):
    # Declaring a figure "gnt"
    fig, gnt = plt.subplots()

    # Setting axes limits
    gnt.set_xlim(0, num_cols)
    gnt.set_ylim(0, 2*len(row_list))
    # Setting axes labels
    gnt.set_xlabel('Hours')
    gnt.set_ylabel('')

    # Setting axes ticks and labels
    gnt.set_xticks([i for i in range(0,int(num_cols))])
    gnt.set_xticklabels([i for i in range(0,int(num_cols))])
    gnt.set_yticks([2*i-1.5 for i in range(1,len(row_list)+1)])
    gnt.set_yticklabels(row_list)
    gnt.grid(True)

    # Setting graph attribute
    colors = ('blue', 'red', 'orange', 'green', 'yellow', 'purple', 'pink', 'teal', 'magenta', 'grey')
    for row in range(len(row_list)):
        bars = []
        for job_id, rowval in solution:
            if row == rowval:
                is_present, start, duration, end = solution[job_id,row]
                if is_present == 1 and duration > 0:
                    gnt.broken_barh([[start,duration]], [2*row+.5,1],
                                    facecolors=colors[(job_id if diffjobs else
                                                       row)%len(colors)],
                                    edgecolor='black')
    plt.tight_layout()
    plt.ion()
    plt.show()
    wait_for_input()
    plt.close()

def plot_binary(row_list, num_cols, diffjobs, duration, solution):
    # Declaring a figure "gnt"
    fig, gnt = plt.subplots()

    # Setting axes limits
    gnt.set_xlim(0, num_cols)
    gnt.set_ylim(0, 2*len(row_list))
    # Setting axes labels
    gnt.set_xlabel('Hours')
    gnt.set_ylabel('')

    # Setting axes ticks and labels
    gnt.set_xticks([i for i in range(0,int(num_cols))])
    gnt.set_xticklabels([i for i in range(0,int(num_cols))])
    gnt.set_yticks([2*i-1.5 for i in range(1,len(row_list)+1)])
    gnt.set_yticklabels(row_list)
    gnt.grid(True)

    # Setting graph attribute
    colors = ('blue', 'red', 'orange', 'green', 'yellow', 'purple', 'pink', 'teal', 'gold', 'grey')
    for row in range(len(row_list)):
        bars = []
        for job_id, rowval, time in solution:
            if row == rowval:
                is_present = solution[job_id,row,time]
                if is_present == 1:
                    gnt.broken_barh([[time,duration]], [2*row+.5,1],
                                    facecolors=colors[(job_id if diffjobs else
                                                       row)%len(colors)],
                                    edgecolor='black')

    plt.tight_layout()
    plt.ion()
    plt.show()
    wait_for_input()
    plt.close()
