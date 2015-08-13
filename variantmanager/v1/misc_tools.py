# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------


class MiscTools:
    
    @staticmethod
    def remove_empty_elements(list_in):
        list_out = [element for element in list_in if len(element) > 0]
        return list_out

    @staticmethod
    def split_list_to_chunks(list_in, num_chunks):

        elems_per_chunk = int(len(list_in) / num_chunks)
        final_list = []

        list_chunk = []
        for elem in range(len(list_in)):
            list_chunk.append(list_in[elem])

            if (elem + 1) % elems_per_chunk == 0:
                final_list.append(list_chunk)
                list_chunk = []

            elif (elem+1) > (elems_per_chunk * num_chunks):
                final_list[-1].append(list_in[elem])

        return final_list

    @staticmethod
    def combine_list_of_lists(list_of_lists):

        list_out = []
        for list_in in list_of_lists:
            list_out = list_out + list_in

        return list_out


