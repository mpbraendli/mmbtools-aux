/* Test program for USRP B200 master_clock_rate
 * setting.
 *
 * Compile with
 *  g++ -Wall -luhd -lboost_system test.cpp -o test
 *
 * Matthias P. Braendli
 * http://mpb.li
 *
 * Code partly taken from ODR-DabMod
 * http://opendigitalradio.org
 */
#include <uhd/utils/thread_priority.hpp>
#include <uhd/utils/safe_main.hpp>
#include <uhd/usrp/multi_usrp.hpp>
#include <boost/thread/thread.hpp>
#include <boost/thread/barrier.hpp>
#include <boost/shared_ptr.hpp>
#include <list>
#include <string>

#include <iostream>
#include <assert.h>
#include <stdexcept>
#include <stdio.h>
#include <time.h>
#include <errno.h>
#include <unistd.h>

typedef std::complex<float> complexf;

const double dab_rate_base = 2048000;

int main(int argc, char **argv)
{
    uhd::set_thread_priority_safe();
    std::string myDevice = "type=b200";

    //create a usrp device
    printf("OutputUHD:Creating the usrp device with: %s...\n",
            myDevice.c_str());

    uhd::usrp::multi_usrp::sptr myUsrp;

    myUsrp = uhd::usrp::multi_usrp::make(myDevice);

    printf("OutputUHD:Using device: %s...\n", myUsrp->get_pp_string().c_str());

    std::cerr << "UHD clock source is " <<
        myUsrp->get_clock_source(0) << std::endl;

    std::cerr << "UHD time source is " <<
        myUsrp->get_time_source(0) << std::endl;

    int mult = 5;

    while (dab_rate_base * mult < 56000000) {

        myUsrp->set_master_clock_rate(dab_rate_base * mult);

        double real_rate = myUsrp->get_master_clock_rate();

        if (real_rate == dab_rate_base * mult) {
            std::cout << "SUCCESS: " << mult << std::endl;
        }
        else {
            std::cout << "FAILURE: " << mult << std::endl;
        }

        mult++;
    }
}

