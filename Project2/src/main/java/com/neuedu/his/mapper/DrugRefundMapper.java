package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.DrugRefund;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;

@Mapper
public interface DrugRefundMapper {

    @Insert("INSERT INTO drug_refund(prescription_id, pharmacist_id, refund_reason, refund_amount, refund_time, create_time) " +
            "VALUES(#{prescriptionId}, #{pharmacistId}, #{refundReason}, #{refundAmount}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(DrugRefund drugRefund);
}
