
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np


# In[54]:


def read_in_logfile(path, vid_lengths):
    pd.read_csv(path, sep='\t', skip_rows=3)
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
    #df = pd.DataFrame({'onset':log['Time'].shift(1).loc[rating_mask].values, 'participant_rating':log.loc[rating_mask]['Code'].values, 'event_type':'button_press', 'duration':0})    
    
    
    #switching it to not be from the row before because if it has a vid tag before it then it will get the wrong onset number
    df = pd.DataFrame({'onset':log['Time'].loc[rating_mask].values, 'participant_rating':log.loc[rating_mask]['Code'].values, 'event_type':'button_press', 'duration':0})    
    #this pretty much fixes it except for the vid_thing - one thing I could do is just get rid of the vid_ rows!! TODO later.
    
    #gets rating substring from participant numbers
    df['participant_rating'] = df['participant_rating'].str.strip().str[-1] #do i have to add a .astype to this?
    
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
            'participant_rating':5}
            combo=combo.append(new_row,ignore_index=True)
        
    combo=combo.sort_values("onset").reset_index(drop=True)

    return(combo)


# In[49]:



ratings_dict= read_in_standard('EA-timing.csv')


# In[3]:


pd.set_option('display.max_rows', 100)
avg=[]
avg[1]


# In[103]:


mask = pd.notnull(combo['trial_type'])
block_start_locs=combo[mask].index.values

#yay so this type of command can output a number for every two seconds, maybe would appenbd an end of trial number at the end? for the final running avg that isnt actually 2 secs
test = np.arange(combo.onset[block_start_locs[0]], combo.end[block_start_locs[0]],step=20000)

#print(test)

#so put this into a for loop!
#need to handle an exception if theres nothing in between - to just keep it at same as prior.
combo.onset.between(test[2],test[3],inclusive=True) & pd.notnull(combo.event_type) #should probably find a better way than nulls to denote different types
combo.loc[combo.onset.between(test[2],test[3],inclusive=True) & pd.notnull(combo.event_type)]

avg=[]
lastval=pd.DataFrame()

#get rid of the -1 eventually lol

#okay so i am sort of getting there? But still have a lot of fixing to do tbh.
for i in range(len(test)-1):
    rows=combo.loc[combo.onset.between(test[i],test[i+1],inclusive=True) & pd.notnull(combo.event_type)]
    if len(rows)==0: #this will never happen at the beginning bc the first timepoint always has a default value
        #lastval=lastval.append(lastval.iloc(i-1))
        avg.append(lastval.iloc(i)) #adds the last value for when theres no avg to calculate
        #print(lastval)
    else:
        #avg.append(calc_avg(rows)) #make a calc_avg function
        lastval=lastval.append(rows.iloc[[-1]])

lastval



combo[combo['onset'].between(combo.onset[block_start_locs[0]], combo.end[block_start_locs[0]])]


# In[53]:


mask = pd.notnull(combo['trial_type']) #selects the beginning of trials/trial headers
block_start_locs=combo[mask].index.values


block_start=combo.onset[block_start_locs[0]]
block_end=combo.end[block_start_locs[0]]

#selects the rows between the start and the end that contain button presses
block = combo[combo['onset'].between(block_start, block_end) & pd.notnull(combo.event_type)] #between is inclusive by default
block_name= combo.movie_name[combo['onset'].between(block_start, block_end) & pd.notnull(combo.movie_name)].astype(str).get(0) 
###############################################################################################

interval = np.arange(combo.onset[block_start_locs[0]], combo.end[block_start_locs[0]],step=20000)


interval=np.append(interval, block_end) #this is to append for the remaining fraction of a second - maybe i dont need to do this

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
        last_val=sub_block.participant_rating.iloc[[-1]]
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
            last_row=row.participant_rating
            ratings.append({'start':start,'end':end,'row_time':row.rating_duration, 'row_start': row.onset, 'block_length':block_length,'rating':row.participant_rating, 'time_held':numerator})#, 'start': start, 'end':end})
            nums=[float(d['rating']) for d in ratings]
            times=[float(d['time_held'])/block_length for d in ratings]
            avg=np.sum(np.multiply(nums,times))
    else:
        avg=last_row
        
    two_s_avg.append(float(avg))

print(two_s_avg)
        
#     if row.onset+row.rating_duration <= test[14]:
#         rating_len.append(rating_duration)
#     elif row.onset+row.rating_duration > test[14]:
#         rating_len.append(test[14]-row.onset)

#     participant_rating.append(row.participant_rating)



#then for each row:
    #if onset<start 
        #and onset+duration>start (just to be safe)
            #numerator = (onset+duration)-start
    #elif onset>=start
        #and onset+duration <= end
            #numerator = duration
        #and onset+duration>end
            #numerator=end-onset
    #rating_value=rating_value :) 
    #also the sum of numerator should = denom

gold_standard=[float(x) for x in ratings_dict[block_name] if x != 'nan']


# In[127]:


start=interval[13]
end=interval[14]
block['onset'].between(start,end)


# In[100]:


#aaah except for things that have too long a rating duration and spill into the last one

#should i pass the previous value into the function as well?

#denom will always be 2 seconds! (wait unless it's at the end of a block aa...)
denom= test[14] - test[13]

rows=combo.loc[combo.onset.between(test[13],test[14],inclusive=True) & pd.notnull(combo.event_type)]

last_row= combo.loc[combo.onset.between(test[12],test[13],inclusive=True) & pd.notnull(combo.event_type)].iloc[[-1]]


rating_len=[]
participant_rating=[]


#OKAY so making an average needs: the rows in this block, plus the rows in the last row - 
#why dont i just select anything with onset between the things, plus the row right before


#then for each row:
    #if onset<start 
        #and onset+duration>start (just to be safe)
            #numerator = (onset+duration)-start
    #elif onset>=start
        #and onset+duration <= end
            #numerator = duration
        #and onset+duration>end
            #numerator=end-onset
    #rating_value=rating_value :) 
    #also the sum of numerator should = denom

#for previous row:
if previous_onset+previous_duration > test[13]:
    rating_len.append((previous_onset+previous_duration) - test[13])
else:
    rating_len.append(0)

participant_rating.append(previous_rating)

for index, row in rows.iterrows():
    #for rows that are in the thing
    if row.onset+row.rating_duration <= test[14]:
        rating_len.append(rating_duration)
    elif row.onset+row.rating_duration > test[14]:
        rating_len.append(test[14]-row.onset)

    participant_rating.append(row.participant_rating)


num=row.participant_rating*(row.rating_duration/denom)if onset+rating_duration < test[14] else participant_rating*((onset - test[14]))






# In[98]:


denom= test[14] - test[13]

rows=combo.loc[combo.onset.between(test[13],test[14],inclusive=True) & pd.notnull(combo.event_type)]


rows.iloc[[-1]]

rows


# In[25]:


#Reads in the log, skipping the first three preamble lines
log=pd.read_csv('/projects/gherman/Experimenting_notebooks/SPN01_CMH_0001-UCLAEmpAcc_part1.log', sep='\t', skiprows=3)


vid_in = pd.read_csv('EA-vid-lengths.csv')

vid_info = format_vid_info(vid_in)
blocks = get_blocks(log, vid_info)
ratings = get_ratings(log)

#add the ratings and the block values together, then sort them and make the index numbers sequential
combo=combine_dfs(blocks,ratings)





#find what index each block starts and ends at, then does some stupid formatting stuff to flatten the array
t=np.array(np.where(pd.notnull(combo['trial_type']))).ravel()

#adds the end of the last trial so i can get starts and ends of everything #delete this if im doing it this way
#t = np.append(t,len(combo["trial_type"])-1)

#creates a dict with trials and start/ends. Next it needs to differentiate between circles and EA and then get the nice values.
[{(combo['trial_type'][t[i]],combo['stim_file'][t[i]]): {'start':t[i],'end':t[i+1]-1}} for i in range(len(t)-1)]
#^okay, so maybe instead it makes sense to include the actual times... or maybe to create an actual df with info about all this.

combo

mask = pd.notnull(combo['trial_type'])
    #combo['end_time']=combo['onset']-combo['onset'].shift(1)

    
    
    

    #so one way to do this would be to make durations visible everywhere

    #yay! fixes the rating for the last button press of a series!
    #gives a SettingWithCopy warning
    #TODO: fix this lol
    #this ends up not assigning a value for the final button press - there must be a more elegant way to do all this
    
    
combo


# In[50]:


[{(combo['trial_type'][t[i]],combo['stim_file'][t[i]]): {'start':(t[i], combo['onset'][t[i]]),'end':(t[i+1]-1,combo['onset'][t[i]]+combo['duration'][t[i]])}} for i in range(len(t)-1)]
combo


mask = pd.notnull(combo['trial_type'])
#combo['end_time']=combo['onset']-combo['onset'].shift(1)

combo['rating_duration']=combo['onset'].shift(-1)-combo['onset'].where(mask==False) #hmm but how do i make the ones in the end of the row? because those actually should calculate from block_end, not from the beginning of the next guy...
#combo['rating_duration']=
combo['block_end']=combo[['onset', 'duration']].sum(axis=1).where(mask==True)
#combo['rating_duration'] = (combo.onset.shift(-1)-combo.onset).where(mask==False)
#combo['end_time']=

#combo[''].apply(lambda x: x[['onset', 'duration']].sum(axis=1) if np.all(pd.notnull(x['trial_type'])) else x)



#df[['onset','duration']].apply(lambda x: my_func(x) if(np.all(pd.notnull(x[1]))) else x, axis = 1)

#combo[['onset','onset'.shift(-1)]].sum(axis=1).where(mask==False)

#pd.DataFrame({'onset':log['Time'].shift(1).loc[rating_mask].values, 'participant_rating':log.loc[rating_mask]['Code'].values, 'event_type':'button_press', 'duration':0})    
#combo['onset']-combo['onset'].shift(1) 
#combo['end_time']=combo[['onset','onset'.shift(-1)]].sum(axis=1).where(mask==False)
#combo
#combo


# In[19]:



#Time col contains the button press onset time in event_type=response, Code col 
#contains the button press' value in rating_mask

#I am not entirely sure that I should be getting the time from the row before, but it kind of makes sense to take the most straightforward one

#101 is the event code for some initial button press or response. We can ignore it. (AT LEAST acc. to the CAMH
#scan. Please cross-reference with others before finalizing)


#the times in this row are EXTREMELY close to the other times. This isn't EEG, I think we're prolly ok
rating_mask = ["rating" in log['Code'][i] for i in range(0,log.shape[0])]  
#RT_mask=  ["Response" in log['Event Type'][i] and log['Code'][i]!="101"  for i in range(0,log.shape[0]-1)]  #this is from when i was doing it the response time way, but idk how i feel abt that

#so now this grabs the timestamp from the row before (which is the actual onset) then applies the rating mask to that list of values
df = pd.DataFrame({'onset':log['Time'].shift(1).loc[rating_mask].values, 'participant_rating':log.loc[rating_mask]['Code'].values, 'event_type':'button_press', 'duration':0})    

df['rating_duration'] = df.onset.shift(-1)-df.onset #this isnt totally correct bc of the stuff.



# In[57]:


df2=blocks.append(df)

df2.sort_values("onset")

log

rating_mask = ["rating" in log['Code'][i] for i in range(0,log.shape[0])]  
log['Time'].shift(1).loc[rating_mask].values


# In[56]:


rating_mask = ["rating" in log['Code'][i] for i in range(0,log.shape[0])]  
log['Time'].shift(1).loc[rating_mask]


# In[ ]:


#HERE LIES THE CHUNK OF JUNK IM MOVING TO THE END

#(combo['trial_type'][t[0]],combo['trial_type'][t[1]-1])
#pd.notnull(combo['trial_type'])
#(starts,ends)=[(t[i],t[i+1]-1) for i in range(len(t)-1)]

#combo.sort_values("onset")
#uses isna in some versions
#combo.isnull()

#combo.sort_values("onset")


#log['Time']=log['Time'].astype(str) #can i read it in initially with strings only? like stringsAsFactors=T in R?

#Finds the start and end times of blocks


#okay so Time from row n-1 + TTime from row n = Time in row n !!! 
#We will subtract Duration of MRI start from all times to give us the time
#(block_starts, block_types) = (log['Time'][] 
                               
 #                              df.loc[df['B'], 'A']

#f['c2'] = df['c1'].apply(lambda x: 10 if x == 'Value' else x)

#def get_button_press(log):

#Time col contains the button press onset time in event_type=response, Code col 
#contains the button press' value in rating_mask

#101 is the event code for some initial button press or response. We can ignore it. (AT LEAST acc. to the CAMH
#scan. Please cross-reference with others before finalizing)

#log['Time'] = log['Time'].astype(str)
#rating_mask = ["rating" in log['Time'][i] for i in range(0,log.shape[0]-1)]  
#response_mask=  ["rating" in log['Code'][i] for i in range(0,log.shape[0]-1)]  

#or "Response" in log['Code'][i]
    
#df = pd.DataFrame({'onset':log.loc[rating_mask]['Time'], 'rating':log.loc[response_mask]['Code']})    

#df
    
#pd.DataFrame{'col1': [1, 2], 
           #  'col2': [3, 4]}

#[[log['Code'][i], log['Time'][i], log['Event Type'][i]] for i in range(0,log.shape[0]-1) if("vid" in log['Code'][i])]

