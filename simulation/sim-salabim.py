import salabim as sim 



class CustomerGenerator(sim.Component):
    def process(self):
        while True:
            Customer().enter(waiting_room)
            self.hold(sim.Uniform(5, 15).sample())


class Customer(sim.Component):
    ...
    # def process(self):
        # self.enter(waitingline)
        # for clerk in clerks:
        #     if clerk.ispassive():
        #         clerk.activate()
        #         break
        # self.passivate()


class Clerk(sim.Component):
    def process(self):
        while True:
            customer = self.from_store(waiting_room)
            self.hold(30)
            # while len(waitingline) == 0:
            #     self.passivate()
            # self.customer = waitingline.pop()
            # self.hold(30)
            # self.customer.activate()


env = sim.Environment(trace=True)

CustomerGenerator()
for _ in range(3):
    Clerk()
# clerks = [Clerk() for _ in range(3)]
# waitingline = sim.Queue('waitingline')
waiting_room = sim.Store('waiting_room')


env.run(till=5000)
# waitingline.print_histograms()
# waitingline.print_info()
# print()
# waitingline.print_statistics()
waiting_room.print_statistics()
waiting_room.print_info()
