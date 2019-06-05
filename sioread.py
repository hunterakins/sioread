import numpy as np
from struct import unpack
from math import ceil,floor

def sioread(**kwargs):
    '''
    Translation of Jit Sarkar's sioread.m to Python
    Hunter Akins
    June 4, 2019

     Input parameters:
    	file_name	:[str]			Name/path to .sio data file to read
    	s_start		:[int](1)		Sample # to begin reading from (default 1)
    	Ns			:[int](1)		Total # of samples to read (default all)
    	Channel		:[int](Nc)		Which channels to read (default all)
    								Channel 0 returns header only, X is empty
    	inMem		:[lgcl](1)		Perform data parsing in ram (default true)
    								False - Disk intensive, memory efficient
    									Blocks read sequentially, keeping only
    									requested channels
    								True  - Disk efficient, memory intensive
    									All blocks read at once, requested
    									channels are selected afterwards
    
     Output parameters:
    	X			:[dbl](Ns,Nc)	Data output matrix
    	Header		:[struct]		Descriptors found in file header

    '''
    if 'fname' not in kwargs.keys():
        raise ValueError("must pass me a filename")
    file_name = kwargs['fname']

    with open(file_name, 'rb') as f:
        # Parameter checking
        s_start = 1
        if 's_start' in kwargs.keys():
            tmp = kwargs['s_start']
            s_start = max(tmp, 0)
       

        if 'Ns' not in kwargs.keys():
            Ns = -1
        else:
            Ns = kwargs['Ns']
            

        if 'channels' not in kwargs.keys():
            channels = []
        else:
            channels = kwargs['channels']
            
        if 'inMem' not in kwargs.keys():
            inMem = True
        else:
            inMem = kwargs['inMem'] # false will read whole file before subsetting

        # Endian check
        endian	=	'>'
        f.seek(28)
        bs	= unpack(endian +  'I', f.read(4))[0]		# should be 32677
        if bs != 32677:
            endian	=	'<'
            bs	=unpack(endian + 'I', f.read(4))[0]	# should be 32677
            if bs != 32677:
                raise ValueError('Problem with byte swap constant:' + str(bs))

        f.seek(0)
        ID	= int(unpack(endian + 'I', f.read(4))[0])	# ID Number
        Nr	= int(unpack(endian + 'I', f.read(4))[0])	# # of Records in File
        BpR	= int(unpack(endian + 'I', f.read(4))[0])	# # of Bytes per Record
        Nc	= int(unpack(endian + 'I', f.read(4))[0])	# # of channels in File
        BpS	= int(unpack(endian + 'I', f.read(4))[0])	# # of Bytes per Sample
        if BpS == 2:
            dype = 'h'
        else:
            dtype = 'f'
        tfReal = unpack(endian + 'I', f.read(4))[0] # 0 = integer, 1 = real
        SpC  = unpack(endian + 'I', f.read(4))[0] # # of Samples per Channel
        bs  = unpack(endian + 'I', f.read(4))[0] # should be 32677
        fname = unpack('24s', f.read(24)) # File name
        comment = unpack('72s', f.read(72)) # Comment String

        RpC  = ceil(Nr/Nc)   # # of Records per Channel
        SpR  = int(BpR/BpS)          # # of Ssmples per Record

        # Header object, for output
        Header = {}
        Header['ID'] = ID
        Header['Nr']  = Nr
        Header['BpR']  = BpR
        Header['Nc']  = Nc
        Header['BpS'] = BpS
        Header['tfReal'] = tfReal
        Header['SpC']  = SpC
        Header['RpC']  = RpC
        Header['SpR']  = SpR
        Header['fname'] = fname
        Header['comment'] = comment
        Header['bs']  = bs
        Header['Description'] = """
                    ID		=	ID Number
                    Nr		=	# of Records in File
                    BpR	=	# of Bytes per Record
                    Nc		=	# of channels in File
                    BpS	=	# of Bytes per Sample
                    tfReal	=	0 - integer, 1 - real
                    SpC	=	# of Samples per Channel
                    fname	=	File name
                    comment=	Comment String
                    bs		=	Endian check value, should be 32677
                    """
            

        # if either channel or # of samples is 0, then return just header
        if (0 in channels) or (Ns == 0):
            X	=	[]
            return X, Header


        # Recheck parameters against header info
        Ns_max = SpC - s_start + 1;
        if	Ns == -1:
            Ns	=	Ns_max			#	fetch all samples from start point
        if Ns > Ns_max:
            print('More samples requested than present in data file. Return max num samples:', Ns_max)
            Ns	=	Ns_max

        # Check validity of Channeli list
        if len(channels) == 0:
            channels	=	list(range(Nc))	#	fetch all channels
        if (len([x for x in channels if (x < 0) or (x > (Nc - 1))]) != 0):
            raise ValueError('Channel #s must be within range 0 to ' + str(Nc - 1))


        ## Read in file according to specified method
        # Calculate file offsets
        # Header is size of 1 Record at beginning of file
        r_hoffset	=	1
        # Starting and total records needed from file
        r_start	=int( floor((s_start-1)/SpR)*Nc + r_hoffset)
        r_total	= int(ceil(Ns/SpR)*Nc)

        # Aggregate loading
        if	inMem:
            # Move to starting location
            print(r_start)
            print(BpR)
            f.seek( r_start*BpR)

            # Read in all records into single column
            if dtype == 'f':
                Data	=	unpack(endian + 'f'*r_total*SpR, f.read( r_total*SpR*4))
            else:
                Data	=	unpack(endian + 'h'*r_total*SpR, f.read( r_total*SpR*2))
            count = len(Data)
            Data = np.array(Data) # cast to numpy array
            if	count != r_total*SpR:
                raise ValueError('Not enough samples read from file')

            #	Reshape data into a matrix of records
            Data	=	np.reshape(Data, (r_total, SpR)).T
            
            #	Select each requested channel and stack associated records
            m	=	int(r_total/Nc *SpR)
            n	=	len(channels)
            X	=	np.zeros((m,n))
            for	i in range(len(channels)):
                chan	=	channels[i]
                blocks = np.arange(chan, r_total, Nc, dtype='int')
                tmp	=	Data[:, blocks]
                X[:,i]	=	tmp.T.reshape(m,1)[:,0]

            # Trim unneeded samples from start and end of matrix
            trim_start	=	int((s_start-1)%SpR)
            if	trim_start != 0:
                X = X[trim_start:,:]
            [m,tmp]	=	np.shape(X)
            if	m > Ns:
                X = X[:int(Ns), :]
            if	m < Ns:
                raise ValueError('Requested # of samples not returned')
            
            
        # Incremental loading
        else:
            print('Not yet implemented incremental loading')

    return X, Header