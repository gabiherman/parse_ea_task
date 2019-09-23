
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np

pd.set_option('display.max_rows', 400) ##REMOVE IN SCRIPT


# In[50]:


def read_in_logfile(path):
    log_file=pd.read_csv(path, sep='\t', skiprows=3)

    time_to_subtract=int(log_file.Time[log_file.Code=='MRI_start'])

    log_file.Time=log_file.Time-time_to_subtract #subtracts mri start times from onset (i think... check what JV did...)
    
    return log_file

def get_blocks(log,vid_info):
    #identifies the video trial types (as opposed to button press events etc)
    mask = ["vid" in log['Code'][i] for i in range(0,log.shape[0])]
    #this isnt totally right lol
    #creates the dataframe with onset times and event types
    df = pd.DataFrame({'onset':log.loc[mask]['Time'], 
                  'trial_type':log.loc[mask]['Event Type'], 
                  'movie_name':log.loc[mask]['Code']})
        
    #adds trial type info
    df['trial_type']=df['movie_name'].apply(lambda x: "circle_block" if "cvid" in x else "EA_block")

    #add durations and convert them into the units here? ms??
    df['duration']=df['movie_name'].apply(lambda x: int(vid_info[x]['duration'])*10000 if x in vid_info else "n/a")

    #I don't actually know what the stim files are called for the circle ones - also these names aren't exact,gotta figure out a way to get exact file names
    df['stim_file']=df['movie_name'].apply(lambda x: vid_info[x]['stim_file'] if x in vid_info else "n/a") 
    
    
    df['end']=df['onset']+df['duration']

        
    return(df)


    
def format_vid_info(vid):
    vid.columns = map(str.lower, vid.columns)
    vid = vid.rename(index={0:"stim_file", 1:"duration"})
    vid = vid.to_dict()
    return(vid)


def read_in_standard(timing_path):
    df = pd.read_csv(timing_path).astype(str)
    df.columns = map(str.lower, df.columns)
    df_dict = df.drop([0,0]).reset_index(drop=True).to_dict(orient='list') #drops the video name
    return(df_dict)

def get_series_standard(gold_standard, block_name):
    
    return([float(x) for x in ratings_dict[block_name] if x != 'nan'])


def get_ratings(log):
    #the times in this row are EXTREMELY close to the other times. This isn't EEG, I think we're prolly ok
    rating_mask = ["rating" in log['Code'][i] for i in range(0,log.shape[0])]  
    #RT_mask=  ["Response" in log['Event Type'][i] and log['Code'][i]!="101"  for i in range(0,log.shape[0]-1)]  #this is from when i was doing it the response time way, but idk how i feel abt that

    #so now this grabs the timestamp from the row before (which is the actual onset) then applies the rating mask to that list of values
    #df = pd.DataFrame({'onset':log['Time'].shift(1).loc[rating_mask].values, 'participant_value':log.loc[rating_mask]['Code'].values, 'event_type':'button_press', 'duration':0})    
    
    
    #switching it to not be from the row before because if it has a vid tag before it then it will get the wrong onset number
    df = pd.DataFrame({'onset':log['Time'].loc[rating_mask].values, 'participant_value':log.loc[rating_mask]['Code'].values, 'event_type':'button_press', 'duration':0})    
    #this pretty much fixes it except for the vid_thing - one thing I could do is just get rid of the vid_ rows!! TODO later.
    
    #gets rating substring from participant numbers
    df['participant_value'] = df['participant_value'].str.strip().str[-1] #do i have to add a .astype to this?
    
    #TODO: probably remove this from this function and rewrite it in the place where i combine the ratings and block info
    #df['rating_duration'] = df.onset.shift(-1)-df.onset #this isnt totally correct bc of the stuff.

    return(df)


def combine_dfs(blocks,ratings):
    combo=blocks.append(ratings).sort_values("onset").reset_index(drop=True)

    mask = pd.notnull(combo['trial_type'])
    #combo['end_time']=combo['onset']-combo['onset'].shift(1)

    combo['rating_duration']=combo['onset'].shift(-1)-combo['onset'].where(mask==False) #hmm but how do i make the ones in the end of the row? because those actually should calculate from block_end, not from the beginning of the next guy...
    #this one is tricky!!

    block_start_locs=combo[mask].index.values

    #so one way to do this would be to make durations visible everywhere

    #can i do for i in block_start_locs

    #yay! fixes the rating for the last button press of a series!
    #gives a SettingWithCopy warning
    #TODO: fix this lol
    #this ends up not assigning a value for the final button press - there must be a more elegant way to do all this
    for i in range(len(block_start_locs)):
        if block_start_locs[i] != 0:
            #maybe i should calculate these vars separately for clarity
            combo.rating_duration[block_start_locs[i]-1]=combo.end[block_start_locs[i-1]] - combo.onset[block_start_locs[i]-1]

            
#adds rows that contain the 5 second at the beginning default value
    for i in block_start_locs:
            new_row={'onset':combo.onset[i],
            'rating_duration':combo.onset[i+1] - combo.onset[i],
            'event_type':'default_rating',
            'duration':0,
            'participant_value':5}
            combo=combo.append(new_row,ignore_index=True)
        
    combo=combo.sort_values("onset").reset_index(drop=True)

    return(combo)



def block_scores(ratings_dict,combo):
    list_of_rows=[]
    summary_vals = {}
    mask = pd.notnull(combo['trial_type']) #selects the beginning of trials/trial headers #i feel like im recalculating that in lots of places, seems bad maybe
    block_start_locs=combo[mask].index.values #i could just append the end to that
    block_start_locs= np.append(block_start_locs, combo.tail(1).index.values, axis=None)

    for idx in range(1, len(block_start_locs)):
            #df['trial_type']=df['movie_name'].apply(lambda x: "circle_block" if "cvid" in x else "EA_block")

        block_start=combo.onset[block_start_locs[idx-1]]
        block_end=combo.end[block_start_locs[idx-1]]

        #selects the rows between the start and the end that contain button presses
        #should just change this to select the rows, idk why not lol

        block = combo.iloc[block_start_locs[idx-1]:block_start_locs[idx]][pd.notnull(combo.event_type)]#between is inclusive by default
        block_name=combo.movie_name.iloc[block_start_locs[idx-1]:block_start_locs[idx]][pd.notnull(combo.movie_name)].reset_index(drop=True).astype(str).get(0)

        ###############################################################################################
        gold=get_series_standard(ratings_dict,block_name)

        if "cvid" in block_name:
            interval = np.arange(combo.onset[block_start_locs[idx-1]], combo.end[block_start_locs[idx-1]],step=40000) #AAA oh no this only applies to the vid not the cvid (put a conditional here)
        else:
            interval = np.arange(combo.onset[block_start_locs[idx-1]], combo.end[block_start_locs[idx-1]],step=20000) #AAA oh no this only applies to the vid not the cvid (put a conditional here)



        #todo: remove print statements lol

        if len(gold) < len(interval):
            interval=interval[:len(gold)]
            print("warning:gold standard is shorter than the number of pt ratings, pt ratings truncated", block_name)
            #todo: insert a warning that the participant ratings were truncated
            #also this doesnt account for a situation where there are less ratings than the gold standard
            #which could absolutely be a thing if the task was truncated
            #gold.extend([gold[-1]]*(len(interval)-len(gold)))

        if len(interval) < len(gold):
            gold=gold[:len(interval)]
            print("warning:number of pt ratings is shorter than the number of gold std,gold std truncated", block_name)
            #todo: insert a warning that the participant ratings were truncated            

        interval=np.append(interval, block_end) #this is to append for the remaining fraction of a second (so that the loop goes to the end i guess...)- maybe i dont need to do this

        #why is this not doing what it is supposed to do.
        #these ifs are NOT working
        two_s_avg=[]
        for x in range(len(interval)-1):
            start=interval[x]
            end=interval[x+1]
            #things that start within the time interval plus the one that starts during the time interval
            sub_block= block[block['onset'].between(start,end) | block['onset'].between(start,end).shift(-1)]
            block_length=end-start
            if len(sub_block) !=0: 
                ratings=[]
                last_val=sub_block.participant_value.iloc[[-1]]
                for index, row in sub_block.iterrows():
                    #for rows that are in the thing
                    if (row.onset < start): #and (row.onset+row.duration)>start: #what's the best order to do these conditionals in?
                        #if (row.onset+row.duration)>start: # this is just to be safe i guess, gonna see what happens if i comment it out
                        numerator=(row.onset+row.rating_duration)-start
                    else:#if row.onset>=start and row.onset<end: #ooo should i do row.onset<end for everything??
                        if (row.onset+row.rating_duration) <= end:
                            numerator=row.rating_duration
                        elif (row.onset+row.rating_duration) > end: 
                            numerator = end - row.onset
                        else:
                            numerator=9999999
                    last_row=row.participant_value
                    #okay so i want to change this to actually create the beginnings of an important row in our df!
                    ratings.append({'start':start,'end':end,'row_time':row.rating_duration, 'row_start': row.onset, 'block_length':block_length,'rating':row.participant_value, 'time_held':numerator})#, 'start': start, 'end':end})
                    nums=[float(d['rating']) for d in ratings]
                    times=[float(d['time_held'])/block_length for d in ratings]
                    avg=np.sum(np.multiply(nums,times))
            else:
                avg=last_row

            #okay so i want to change this to actually create the beginnings of an important row in our df!
            two_s_avg.append(float(avg))
            #list_of_rows.append({'event_type':"two_sec_avg",'block_name':block_name, 'participant_value':float(avg),'onset':start,'duration':end-start, 'gold_std': gold[x]})
            list_of_rows.append({'event_type':"two_sec_avg", 'participant_value':float(avg),'onset':start,'duration':end-start, 'gold_std': gold[x]})
            #removed block_name from above
            
        n_button_press=len(block[block.event_type=='button_press'].index)
        print(n_button_press)
        block_score=np.corrcoef(gold,two_s_avg)[1][0] 
        key=str(block_name)
        summary_vals.update({key:{'n_button_press':int(n_button_press),'block_score':block_score,'onset':block_start,'duration':block_end-block_start}})
        #summary_vals.append(block_name:{'block_score':block_score,'block_name':block_name,'onset':block_start,'duration':block_end-block_start}) #i can probably not recalculate duration, just gotta remember how
    return(list_of_rows,summary_vals)



# In[53]:


#Reads in the log, skipping the first three preamble lines

log = read_in_logfile('/projects/gherman/Experimenting_notebooks/SPN01_CMH_0004-UCLAEmpAcc_part2.log')
vid_in = pd.read_csv('EA-vid-lengths.csv')

vid_info = format_vid_info(vid_in)
blocks = get_blocks(log, vid_info)
ratings = get_ratings(log)

#add the ratings and the block values together, then sort them and make the index numbers sequential
combo=combine_dfs(blocks,ratings)

ratings_dict= read_in_standard('EA-timing.csv')

two_s_chunks,scores= block_scores(ratings_dict,combo) #okay so i need to fix the naming here 

combo['block_score']=np.nan
combo['n_button_press']=np.nan

#combo.ix[pd.notnull(combo.trial_type), 'block_score']=

#df[df.index.isin(a_list) & df.a_col.isnull()]

combo = combo.append(two_s_chunks).sort_values("onset").reset_index(drop=True) #this needs to be fixed etc #need to sort according to name too...

test = combo.ix[pd.notnull(combo.stim_file)]

for index, row in test.iterrows():
    combo.block_score.ix[index]=scores[row['movie_name']]['block_score']
    combo.n_button_press.ix[index]=scores[row['movie_name']]['n_button_press']
    combo.event_type.ix[index]='block_summary'
   

    
    
combo

#NOTE" 
#ok so tomorrow ive gotta figure out that error :( ) it occurs with 0004 part 2

#I don't think the weighted average is being calculated correctly... -nvm it is! yay!


# In[ ]:


#i'm wondering if i should maybe think more carefully about my architecture here in terms of what i need to calculate where.might try to refine this. 


# In[36]:


combo.iloc[45:62]

idx=1
block_name=combo.movie_name.iloc[block_start_locs[idx-1]:block_start_locs[idx]][pd.notnull(combo.movie_name)].astype(str).get(0) 
block_name


# In[23]:


[gold[-1]]*(len(interval)-len(gold))


# In[96]:


np.corrcoef(gold,two_s_avg)[1][0]


# In[53]:


#ratings,scores=block_scores(ratings_dict,combo)
combo.tail(1).index.values


# In[34]:





# In[47]:


n_button_press=len(block[block.event_type=='button_press'].index)
n_button_press

block
