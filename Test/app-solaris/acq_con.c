#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <string.h>
#include <time.h>
#define __STDC_FORMAT_MACROS
#include <inttypes.h>
#include "redpitaya/rp.h"

#define nsec_in_sec 1000000000ULL
#define million 1000000UL
bool stop;
bool enabled_timestamps;
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
	static uint64_t buffer_fill_time;
	static struct timespec start_acq, stop_acq, rem, req;

	defineSignals();
	if (parseArgs(argc, argv)) raise(SIGINT);

	openTimeStampsFile();
	openBuffFile();
	initRedPitaya();

	printf("%llu\n", nsec_in_sec);
  /* mount sd-card in rw mode */
  system("rw");
  /* allocate memory buffer */
  int16_t *buff = (int16_t *)malloc(array_size * sizeof(int16_t));
	/*  */
	buffer_fill_time = array_size * nsec_in_sec * decimation / (125 * million);

	printf("Starting!\n");
	/* acquire till stop */
	while(!stop)
	{
	    /* Get the whole buffer into buf */
			raise(SIGUSR1);
			clock_gettime(CLOCK_REALTIME, &start_acq);
    	rp_AcqGetOldestDataRaw(channel, &array_size, buff);
	    saveBuffToFile(buff, array_size);
			clock_gettime(CLOCK_REALTIME, &stop_acq);
			//rem.tv_sec = stop_acq.tv_sec - start_acq.tv_sec;
			//rem.tv_nsec = stop_acq.tv_nsec - start_acq.tv_nsec;
			timespec_diff(&start_acq, &stop_acq, &rem);
			/* If saving buffer took too long time, then exit too avoid losing data */
			uint32_t acq_time = (nsec_in_sec * rem.tv_sec + rem.tv_nsec);
			if( acq_time > buffer_fill_time )
			{
				printf("Acquisition took longer then buffer fills,"
				 "exiting to prevent data corruption!\n");
				printf("%lf buffer: %"PRIu64"\n", (10e9 * rem.tv_sec + rem.tv_nsec),
				 buffer_fill_time);
				raise(SIGINT);
			}
			else
			{
			/* sleep to let buffer fill with new data */
				rem.tv_nsec = buffer_fill_time - rem.tv_nsec;
				nanosleep(&rem, &req);
			}
  }

	printf("Stopping");
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
	}

	for(int i = 0; i < size; i++)
			fprintf(data_file, "%d\n", buffer[i]);
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
	if( argc < 4 )
	{
		printf("Usage: ./acquireContinous CH Decimation AbsolutePathToDataFile [Optional: -t enables timestamps]\n");
		return 1;
	}

	if ( argv[1] == 0)
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

	if ( argc == 5 )
	{
		if ( strcmp(argv[4],"-t") == 0 )
		{
			enabled_timestamps=1;
			printf("Enabled timestamps\n");
		}
	}

	return 0;

}
