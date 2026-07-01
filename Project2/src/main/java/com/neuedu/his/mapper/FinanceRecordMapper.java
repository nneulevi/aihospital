package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.FinanceRecord;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface FinanceRecordMapper {

    @Insert("INSERT INTO finance_record(record_no, register_id, record_type, total_amount, item_count, charge_method, operator_id, create_time) " +
            "VALUES(#{recordNo}, #{registerId}, #{recordType}, #{totalAmount}, #{itemCount}, #{chargeMethod}, #{operatorId}, CURRENT_TIMESTAMP)")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(FinanceRecord financeRecord);

    @Select("SELECT * FROM finance_record WHERE id = #{id}")
    FinanceRecord selectById(Long id);
}
