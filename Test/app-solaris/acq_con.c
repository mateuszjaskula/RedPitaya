#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#define __STDC_FORMAT_MACROS
#include <inttypes.h>
#include "redpitaya/rp.h"

#define nsec_in_sec 1000000000ULL
#define million 1000000UL

bool stop;
bool enabled_timestamps;
bool enabled_fsync;
FILE* time_stamps_file;
FILE* data_file;
int rp_decimation = RP_DEC_1024;
int decimation = 1024;
int channel = RP_CH_1;
char *filePath = "/opt/data.txt";

void saveTimeStamp(int sig);
void quitHandler(int sig){ stop = 1; }
void openTimeStampsFile()
{
	time_stamps_file = fopen("/tmp/ram/timestamps", "ab");
}
void closeTimeStampsFile(){	fclose(time_stamps_file); }
void saveBuffToFile(int16_t * buffer, uint32_t size);
int parseArgs(int argc, char **argv);
void openBuffFile();
void closeBuffFile();
void defineSignals();
void cleanUpResources(int16_t* buff);
void initRedPitaya();
void timespec_diff(struct timespec *start, struct timespec *stop,
                   struct timespec *result);

int main(int argc, char **argv)
{
  static uint32_t array_size = 16 * 1024; //Current buffer size.
	static uint64_t buffer_fill_time_ns;
	static struct timespec start_acq, stop_acq, rem, req;

	defineSignals();
	if (parseArgs(argc, argv)) raise(SIGINT);

	openTimeStampsFile();
	openBuffFile();
	initRedPitaya();

  /*
		mount sd-card in rw mode,
	  kill webserver to prevent data corruption,
		synchronize I/O buffer_fill_time_ns
	*/
  system("rw");
	system("killall nginx");
	system("sync");
  /* allocate memory buffer */
  int16_t *buff = (int16_t *)malloc(array_size * sizeof(int16_t));
	/*  */
	buffer_fill_time_ns = array_size * nsec_in_sec * decimation / (125 * million);

	printf("Starting!\n");
	/* acquire till stop */
	while(!stop)
	{
	    /* Get the whole buffer into buf */
			//raise(SIGUSR1);
			saveTimeStamp(SIGUSR1);
			clock_gettime(CLOCK_REALTIME, &start_acq);
    	rp_AcqGetOldestDataRaw(channel, &array_size, buff);
	    saveBuffToFile(buff, array_size);
			clock_gettime(CLOCK_REALTIME, &stop_acq);
			//rem.tv_sec = stop_acq.tv_sec - start_acq.tv_sec;
			//rem.tv_nsec = stop_acq.tv_nsec - start_acq.tv_nsec;
			timespec_diff(&start_acq, &stop_acq, &rem);
			/* If saving buffer took too long time, then exit too avoid losing data */
			uint32_t acq_time_ns = (nsec_in_sec * rem.tv_sec + rem.tv_nsec);
			/* sleep to let buffer fill with new data */
			rem.tv_sec = (buffer_fill_time_ns - acq_time_ns) / nsec_in_sec;
			rem.tv_nsec = buffer_fill_time_ns - acq_time_ns;
			if( acq_time_ns > buffer_fill_time_ns )
			{
				printf("Warning Acquisition took longer then buffer fills \n");
				printf("%"PRIu32" buffer: %"PRIu64"\n", acq_time_ns, buffer_fill_time_ns);
				/* Don't sleep if we are already losing any samples */
				rem.tv_sec = 0;
				rem.tv_nsec = 0;
			}


			nanosleep(&rem, &req);
  }

	printf("Stopping!\n");
	system("sync");
	system("nginx");
	cleanUpResources(buff);
  return 0;
}

void cleanUpResources(int16_t* buff)
{
	/* Releasing resources */
	free(buff);
	rp_Release();
	closeTimeStampsFile();
}

void initRedPitaya()
{
	printf("Configuring RedPitaya\n");
	/* Print error, if rp_Init() function failed */
	if (rp_Init() != RP_OK)
	{
		fprintf(stderr, "Rp api init failed!n");
		raise(SIGINT);
	}

	rp_AcqReset();
	if(rp_AcqSetTriggerSrc(RP_TRIG_SRC_DISABLED))
	{
		printf("Couldn't set trigger! Exiting\n");
		raise(SIGINT);
	}

	if(rp_AcqSetDecimation(rp_decimation))
	{
		printf("Couldn't set decimation! Exiting\n");
		raise(SIGINT);
	}

	if(rp_AcqStart())
	{
		printf("Couldn't start acquisition! Exiting\n");
		raise(SIGINT);
	}
}
void timespec_diff(struct timespec *start, struct timespec *stop,
                   struct timespec *result)
{
    if ((stop->tv_nsec - start->tv_nsec) < 0) {
        result->tv_sec = stop->tv_sec - start->tv_sec - 1;
        result->tv_nsec = stop->tv_nsec - start->tv_nsec + nsec_in_sec;
    } else {
        result->tv_sec = stop->tv_sec - start->tv_sec;
        result->tv_nsec = stop->tv_nsec - start->tv_nsec;
    }
    return;
}

void defineSignals()
{
	signal(SIGTERM, quitHandler);
	signal(SIGINT, quitHandler);
	signal(SIGUSR1, saveTimeStamp);
}

void saveTimeStamp(int sig)
{
	/* Time struct used for experiments */
	static struct timespec last_time;
	static long long time_stamp;
	static struct timespec curr_time;
	clock_gettime(CLOCK_REALTIME, &curr_time);

	/* check if this is first timestamp in runtime, if so only save timestamp */
	if( last_time.tv_nsec != 0 || last_time.tv_sec !=0 )
	{
		time_stamp = (curr_time.tv_sec - last_time.tv_sec) * nsec_in_sec
		+ ((curr_time.tv_nsec - last_time.tv_nsec));
		fprintf(time_stamps_file, "%lld, \n", time_stamp);
	}

	last_time = curr_time;
}

void saveBuffToFile(int16_t *buffer, uint32_t size)
{
	if ( enabled_timestamps )
	{
		static unsigned long long timestamp;
		static struct timespec curr_time;
		int offset = 10e9 / (125 * 10e6 / decimation);
		clock_gettime(CLOCK_REALTIME, &curr_time);
		timestamp = (curr_time.tv_sec) * nsec_in_sec + (curr_time.tv_nsec);

		for(int i = 0; i < size; i++)
			fprintf(data_file, "%llu, %d\n", (timestamp + i*offset), buffer[i]);

		if (enabled_fsync)
			fsync(fileno(data_file));

		return;
	}

	for(int i = 0; i < size; i++)
			fprintf(data_file, "%d\n", buffer[i]);

	if (enabled_fsync)
		fsync(fileno(data_file));

	return;
}

void openBuffFile()
{
	data_file = fopen(filePath, "ab+");
	if(data_file != NULL)printf("File opened!\n");
}

void closeBuffFile()
{
	fclose(data_file);
}

int parseArgs(int argc, char **argv)
{
	printf("Usage: ./acquireContinous CH Decimation AbsolutePathToDataFile \n"
	" [Optional: -t enables timestamps -s enables fsync on data file]\n");
	if( argc < 4 )
	{
		return 1;
	}

	if ( atoi(argv[1]) == 0)
	{
		channel = RP_CH_1;
		printf("Setting channel to %d\n", RP_CH_1);
	}
	else if ( atoi(argv[1]) == 1)
	{
		channel = RP_CH_2;
		printf("Setting channel to %d\n", RP_CH_2);
	}
	else
	{
		printf("Error: Wrong Channel specified\n");
		return 1;
	}

	if ( atoi(argv[2]) == 1 )
	{
		decimation = 1;
		rp_decimation = RP_DEC_1;
		printf("Setting decimation to %d\n", decimation);
	}
	else if ( atoi(argv[2]) == 8 )
	{
		decimation = 8;
		rp_decimation = RP_DEC_8;
		printf("Setting decimation to %d\n", decimation);
	}
	else if ( atoi(argv[2]) == 64 )
	{
		decimation = 64;
		rp_decimation = RP_DEC_64;
		printf("Setting decimation to %d\n", decimation);
	}
	else if ( atoi(argv[2]) == 1024 )
	{
		decimation = 1024;
		rp_decimation = RP_DEC_1024;
		printf("Setting decimation to %d\n", decimation);
	}
	else if ( atoi(argv[2]) == 65536 )
	{
		decimation = 65536;
		rp_decimation = RP_DEC_65536;
		printf("Setting decimation to %d\n", decimation);
	}
	else
	{
		printf("Error: Wrong Decimation specified\n");
		return 1;
	}

	filePath = argv[3];
	if ( filePath[0] != '/' )
		printf("Warning: filePath is probably not absolute!\n"
		"This may lead to errors!\n");

	if ( argc >= 5 )
	{
		if ( strcmp(argv[4],"-t") == 0 )
		{
			enabled_timestamps=1;
			printf("Enabled timestamps\n");
		}
		else if ( strcmp(argv[4],"-s") == 0 )
		{
			enabled_fsync=1;
			printf("Enabled fsync\n");
		}
	}
	
	if ( argc == 6 )
	{
		if ( strcmp(argv[5],"-t") == 0 )
		{
			enabled_timestamps=1;
			printf("Enabled timestamps\n");
		}
		else if ( strcmp(argv[5],"-s") == 0 )
		{
			enabled_fsync=1;
			printf("Enabled fsync\n");
		}
	}

	return 0;
}
